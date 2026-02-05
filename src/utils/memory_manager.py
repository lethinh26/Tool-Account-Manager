import gc
import sys
from typing import Any, Dict
import weakref


class MemoryManager:
    """optimization"""
    
    def __init__(self):
        self._weak_refs: Dict[str, weakref.ref] = {}
    
    @staticmethod
    def force_garbage_collection() -> Dict[str, int]:
        collected = {
            'gen0': gc.collect(0),
            'gen1': gc.collect(1),
            'gen2': gc.collect(2)
        }
        return collected
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss / 1024 / 1024,  # mb
            'vms': memory_info.vms / 1024 / 1024, 
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available / 1024 / 1024 
        }
    
    @staticmethod
    def optimize_images(image_data: bytes, max_size: int = 500) -> bytes:
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_data))
            
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except:
            return image_data
    
    def register_weak_reference(self, key: str, obj: Any) -> None:
        self._weak_refs[key] = weakref.ref(obj)
    
    def get_weak_reference(self, key: str) -> Any:
        if key in self._weak_refs:
            return self._weak_refs[key]()
        return None
    
    @staticmethod
    def clear_cache(obj: Any) -> None:
        if hasattr(obj, '__dict__'):
            cache_attrs = [
                attr for attr in obj.__dict__
                if attr.startswith('_cache_') or attr.startswith('_cached_')
            ]
            for attr in cache_attrs:
                delattr(obj, attr)
    
    @staticmethod
    def optimize_list(items: list, chunk_size: int = 1000):
        for i in range(0, len(items), chunk_size):
            yield items[i:i + chunk_size]
    
    @staticmethod
    def limit_string_length(text: str, max_length: int = 1000) -> str:

        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

memory_manager = MemoryManager()
