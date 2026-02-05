import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, Coroutine
import functools


class AsyncManager:
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = None
    
    def run_async(self, func: Callable, *args, **kwargs) -> Any:
        return self.executor.submit(func, *args, **kwargs)
    
    def run_multiple_async(self, tasks: list) -> list:
        futures = []
        for func, args, kwargs in tasks:
            future = self.executor.submit(func, *args, **kwargs)
            futures.append(future)
        return futures
    
    def wait_all(self, futures: list, timeout: float = None) -> list:
        results = []
        for future in futures:
            try:
                result = future.result(timeout=timeout)
                results.append(result)
            except Exception as e:
                results.append(e)
        return results
    
    def shutdown(self) -> None:
        self.executor.shutdown(wait=True)


def async_operation(ui_callback: Callable = None):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            executor = ThreadPoolExecutor(max_workers=1)
            
            def run_with_callback():
                try:
                    result = func(*args, **kwargs)
                    if ui_callback:
                        ui_callback(result)
                    return result
                except Exception as e:
                    if ui_callback:
                        ui_callback(e)
                    raise
            
            return executor.submit(run_with_callback)
        
        return wrapper
    return decorator


async_manager = AsyncManager()
