from typing import Any, Callable, Dict, Type, Optional
from threading import Lock


class Container:    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, bool] = {}
        self._lock = Lock()
    
    def register(self, service_type: Type, implementation: Any, singleton: bool = True) -> None:
        with self._lock:
            if callable(implementation) and not isinstance(implementation, type):
                self._factories[service_type] = implementation
                self._singletons[service_type] = singleton
            else:
                self._services[service_type] = implementation
                self._singletons[service_type] = True
    
    def resolve(self, service_type: Type) -> Any:
        with self._lock:
            if service_type in self._services:
                return self._services[service_type]
            
            if service_type in self._factories:
                instance = self._factories[service_type]()
                
                if self._singletons.get(service_type, True):
                    self._services[service_type] = instance
                
                return instance
            
            raise KeyError(f"Service {service_type} is not registered")
    
    def is_registered(self, service_type: Type) -> bool:
        return service_type in self._services or service_type in self._factories
    
    def clear(self) -> None:
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()


container = Container()
