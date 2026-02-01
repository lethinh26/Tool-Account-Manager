import socket
import threading
import requests
from typing import Dict, Optional
import time


class LocalProxyServer:
    """Local proxy server forwards to remote proxy"""
    
    def __init__(self, remote_proxy: Dict, local_port: int = None):
        self.remote_proxy = remote_proxy
        self.local_port = local_port or self._find_free_port()
        self.server_socket = None
        self.running = False
        self.thread = None
        
    def _find_free_port(self) -> int:
        """Find free port on localhost"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def start(self):
        """Start the local proxy server"""
        if self.running:
            return self.local_port
        
        self.running = True
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        
        max_wait = 5 
        waited = 0
        while waited < max_wait:
            if self._check_server_ready():
                print(f"Local proxy server is ready on port {self.local_port}")
                return self.local_port
            time.sleep(0.1)
            waited += 0.1
        
        print(f"Warning: Server may not be fully ready yet")
        return self.local_port
    
    def _check_server_ready(self) -> bool:
        """Check server ready connections"""
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(1)
            result = test_sock.connect_ex(('127.0.0.1', self.local_port))
            test_sock.close()
            return result == 0
        except:
            return False
    
    def _run_server(self):
        """Run the proxy server"""
        try:
            import http.server
            import socketserver
            
            class SilentTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
                allow_reuse_address = True
                daemon_threads = True
                
                def handle_error(self, request, client_address):
                    """Log errors without full traceback"""
                    import sys
                    import traceback
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    if exc_type and exc_type.__name__ != 'ConnectionAbortedError':
                        print(f"Server error: {exc_value}")
                        traceback.print_exc()
            
            class ProxyHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, remote_proxy=None, **kwargs):
                    self.remote_proxy = remote_proxy
                    super().__init__(*args, **kwargs)
                
                def do_CONNECT(self):
                    """Handle HTTPS CONNECT requests"""
                    try:
                        host, port = self.path.split(':')
                        port = int(port)
                        
                        print(f"CONNECT request: {host}:{port}")
                        
                        remote_sock = self._connect_through_proxy(host, port)
                        
                        if remote_sock:
                            print(f"Connected to {host}:{port} via proxy")
                            self.send_response(200, 'Connection Established')
                            self.end_headers()
                            
                            self._forward_data(self.connection, remote_sock)
                        else:
                            print(f"Failed to connect to {host}:{port}")
                            try:
                                self.send_error(502, 'Bad Gateway')
                            except:
                                pass 
                    except Exception as e:
                        print(f"CONNECT error ({self.path}): {e}")
                        import traceback
                        traceback.print_exc()
                        try:
                            self.send_error(502, str(e))
                        except:
                            pass  
                
                def do_GET(self):
                    """Handle HTTP GET requests"""
                    try:
                        self._proxy_request('GET')
                    except:
                        pass
                
                def do_POST(self):
                    """Handle HTTP POST requests"""
                    try:
                        self._proxy_request('POST')
                    except:
                        pass
                
                def _proxy_request(self, method):
                    """Proxy HTTP requests through remote proxy"""
                    try:
                        proxy_url = self._build_proxy_url()
                        proxies = {
                            'http': proxy_url,
                            'https': proxy_url
                        }
                        
                        headers = {k: v for k, v in self.headers.items()}
                        headers.pop('Proxy-Connection', None)
                        
                        if method == 'GET':
                            response = requests.get(
                                self.path,
                                headers=headers,
                                proxies=proxies,
                                timeout=30,
                                stream=True
                            )
                        elif method == 'POST':
                            content_length = int(self.headers.get('Content-Length', 0))
                            body = self.rfile.read(content_length) if content_length > 0 else None
                            response = requests.post(
                                self.path,
                                headers=headers,
                                data=body,
                                proxies=proxies,
                                timeout=30,
                                stream=True
                            )
                        
                        self.send_response(response.status_code)
                        for header, value in response.headers.items():
                            if header.lower() not in ['transfer-encoding', 'content-encoding']:
                                self.send_header(header, value)
                        self.end_headers()
                        
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                self.wfile.write(chunk)
                    
                    except Exception as e:
                        print(f"{method} error: {e}")
                        try:
                            self.send_error(502, str(e))
                        except:
                            pass 
                
                def _build_proxy_url(self):
                    """Build proxy URL from remote proxy config"""
                    p = self.remote_proxy
                    protocol = p['protocol']
                    
                    if p.get('username') and p.get('password'):
                        return f"{protocol}://{p['username']}:{p['password']}@{p['host']}:{p['port']}"
                    else:
                        return f"{protocol}://{p['host']}:{p['port']}"
                
                def _connect_through_proxy(self, host, port):
                    """Connect remote proxy using proper SOCKS5/HTTP protocol"""
                    try:
                        p = self.remote_proxy
                        
                        if p['protocol'] in ['socks5', 'socks4']:
                            import struct
                            
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(30)
                            
                            print(f"Connecting to SOCKS5 proxy {p['host']}:{p['port']}")
                            sock.connect((p['host'], p['port']))
                            
                            if p['protocol'] == 'socks5':
                                if p.get('username') and p.get('password'):
                                    sock.sendall(b'\x05\x02\x00\x02')
                                    print(f"Sent SOCKS5 greeting with auth methods")
                                else:
                                    sock.sendall(b'\x05\x01\x00')
                                    print(f"Sent SOCKS5 greeting without auth")
                                
                                response = sock.recv(2)
                                if len(response) != 2 or response[0] != 0x05:
                                    print(f"Invalid SOCKS5 response: {response.hex()}")
                                    sock.close()
                                    return None
                                
                                method = response[1]
                                print(f"SOCKS5 server selected method: {method}")
                                
                                if method == 0x02:  # Username/Password
                                    if not p.get('username') or not p.get('password'):
                                        print("Proxy requires auth but no credentials provided")
                                        sock.close()
                                        return None
                                    
                                    username = p['username'].encode()
                                    password = p['password'].encode()
                                    auth_request = struct.pack('B', 1)  # ver
                                    auth_request += struct.pack('B', len(username)) + username
                                    auth_request += struct.pack('B', len(password)) + password
                                    
                                    sock.sendall(auth_request)
                                    print(f"Sent auth: user={p['username']}, pass=***")
                                    
                                    auth_response = sock.recv(2)
                                    if len(auth_response) != 2 or auth_response[1] != 0x00:
                                        print(f"SOCKS5 auth failed: {auth_response.hex()}")
                                        sock.close()
                                        return None
                                    
                                    print("SOCKS5 authentication successful")
                                
                                elif method == 0xFF:  # No acceptable methods
                                    print("SOCKS5 proxy rejected all auth methods")
                                    sock.close()
                                    return None
                                
                                connect_request = b'\x05\x01\x00'  # Version, CONNECT, Reserved
                                
                                connect_request += b'\x03'
                                host_bytes = host.encode()
                                connect_request += struct.pack('B', len(host_bytes)) + host_bytes
                                connect_request += struct.pack('>H', port)
                                
                                sock.sendall(connect_request)
                                print(f"Sent SOCKS5 CONNECT to {host}:{port}")
                                
                                response = sock.recv(4)
                                if len(response) != 4:
                                    print(f"Invalid SOCKS5 CONNECT response length")
                                    sock.close()
                                    return None
                                
                                if response[1] != 0x00:  # Succ
                                    error_codes = {
                                        0x01: "General SOCKS server failure",
                                        0x02: "Connection not allowed by ruleset",
                                        0x03: "Network unreachable",
                                        0x04: "Host unreachable",
                                        0x05: "Connection refused",
                                        0x06: "TTL expired",
                                        0x07: "Command not supported",
                                        0x08: "Address type not supported"
                                    }
                                    error = error_codes.get(response[1], f"Unknown error {response[1]}")
                                    print(f"SOCKS5 CONNECT failed: {error}")
                                    sock.close()
                                    return None
                                
                                atyp = response[3]
                                if atyp == 0x01:  # IPv4
                                    sock.recv(6)  # 4 bytes IP + 2 bytes port
                                elif atyp == 0x03:  # Domain
                                    addr_len = struct.unpack('B', sock.recv(1))[0]
                                    sock.recv(addr_len + 2)  # domain + port
                                elif atyp == 0x04:  # IPv6
                                    sock.recv(18)  # 16 bytes IP + 2 bytes port
                                
                                print(f"SOCKS5 tunnel established to {host}:{port}")
                                return sock
                            
                            else:  # SOCKS4
                                print("SOCKS4 not fully implemented, use SOCKS5")
                                sock.close()
                                return None
                        
                        # HTTP/HTTPS 
                        elif p['protocol'] in ['http', 'https']:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.settimeout(30)
                            
                            print(f"Connecting to HTTP proxy {p['host']}:{p['port']}")
                            sock.connect((p['host'], p['port']))
                            
                            connect_request = f"CONNECT {host}:{port} HTTP/1.1\r\n"
                            connect_request += f"Host: {host}:{port}\r\n"
                            
                            if p.get('username') and p.get('password'):
                                import base64
                                credentials = f"{p['username']}:{p['password']}"
                                encoded = base64.b64encode(credentials.encode()).decode()
                                connect_request += f"Proxy-Authorization: Basic {encoded}\r\n"
                                print(f"HTTP proxy auth: {p['username']}")
                            
                            connect_request += "\r\n"
                            
                            sock.sendall(connect_request.encode())
                            print(f"Sent HTTP CONNECT to {host}:{port}")
                            
                            response = b""
                            while b"\r\n\r\n" not in response:
                                chunk = sock.recv(1024)
                                if not chunk:
                                    break
                                response += chunk
                            
                            response_str = response.decode('utf-8', errors='ignore')
                            status_line = response_str.split('\r\n')[0]
                            
                            print(f"HTTP proxy response: {status_line}")
                            
                            if '200' in status_line:
                                print(f"HTTP tunnel established to {host}:{port}")
                                return sock
                            else:
                                print(f"HTTP CONNECT failed: {status_line}")
                                sock.close()
                                return None
                        
                        else:
                            print(f"Unsupported proxy protocol: {p['protocol']}")
                            return None
                            
                    except Exception as e:
                        print(f"Proxy connection error to {host}:{port}: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                def _forward_data(self, client_sock, remote_sock):
                    """Bidirectional data forwarding"""
                    def forward(source, destination):
                        try:
                            while True:
                                data = source.recv(4096)
                                if not data:
                                    break
                                destination.sendall(data)
                        except:
                            pass
                        finally:
                            try:
                                source.close()
                                destination.close()
                            except:
                                pass
                    
                    t1 = threading.Thread(target=forward, args=(client_sock, remote_sock))
                    t2 = threading.Thread(target=forward, args=(remote_sock, client_sock))
                    t1.daemon = True
                    t2.daemon = True
                    t1.start()
                    t2.start()
                    t1.join()
                    t2.join()
                
                def log_message(self, format, *args):
                    pass
            
            handler = lambda *args, **kwargs: ProxyHandler(*args, remote_proxy=self.remote_proxy, **kwargs)
            
            with SilentTCPServer(('127.0.0.1', self.local_port), handler) as httpd:
                self.server_socket = httpd
                print(f"Local proxy server started on 127.0.0.1:{self.local_port}")
                print(f"Routing to {self.remote_proxy['protocol']}://{self.remote_proxy['host']}:{self.remote_proxy['port']}")
                
                httpd.serve_forever(poll_interval=0.5)
        
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """Stop local proxy server"""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.shutdown()
            except:
                pass
            try:
                self.server_socket.server_close()
            except:
                pass
            finally:
                self.server_socket = None
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None
    
    def get_local_proxy_url(self) -> str:
        """Get local proxy URL"""
        return f"http://127.0.0.1:{self.local_port}"


class LocalProxyManager:
    """Manage multiple local proxy servers"""
    
    def __init__(self):
        self.active_servers = {}  # account_id -> LocalProxyServer
    
    def create_local_proxy(self, account_id: str, remote_proxy: Dict) -> str:
        """Create local proxy server for an account"""
        # Stop existing server if any
        if account_id in self.active_servers:
            self.stop_local_proxy(account_id)
        
        server = LocalProxyServer(remote_proxy)
        local_port = server.start()
        
        self.active_servers[account_id] = server
        
        return f"http://127.0.0.1:{local_port}"
    
    def stop_local_proxy(self, account_id: str):
        """Stop local proxy server account"""
        if account_id in self.active_servers:
            self.active_servers[account_id].stop()
            del self.active_servers[account_id]
    
    def stop_all(self):
        """Stop all local proxy servers"""
        for account_id in list(self.active_servers.keys()):
            self.stop_local_proxy(account_id)
    
    def get_local_proxy(self, account_id: str) -> Optional[str]:
        """Get local proxy URL for account"""
        if account_id in self.active_servers:
            return self.active_servers[account_id].get_local_proxy_url()
        return None
