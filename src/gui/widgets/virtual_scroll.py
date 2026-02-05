import customtkinter as ctk
from typing import Callable, List, Any, Optional


class VirtualScrollFrame(ctk.CTkScrollableFrame):
    """Virtual scrolling render visible"""
    
    def __init__(
        self,
        master,
        item_height: int = 40,
        create_item_func: Callable[[Any, ctk.CTkFrame], None] = None,
        buffer_size: int = 5,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        
        self.item_height = item_height
        self.create_item_func = create_item_func
        self.buffer_size = buffer_size
        
        self.items: List[Any] = []
        self.visible_widgets: dict = {}
        self.first_visible_index = 0
        self.last_visible_index = 0
        
        self.bind("<Configure>", self._on_scroll)
        self._scrollbar.configure(command=self._on_scrollbar)
    
    def set_items(self, items: List[Any]) -> None:
        self.items = items
        self._update_visible_items()
    
    def append_item(self, item: Any) -> None:
        self.items.append(item)
        self._update_visible_items()
    
    def insert_item(self, index: int, item: Any) -> None:
        self.items.insert(index, item)
        self._update_visible_items()
    
    def remove_item(self, index: int) -> None:
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._update_visible_items()
    
    def clear_items(self) -> None:
        self.items.clear()
        self._clear_visible_widgets()
    
    def _on_scroll(self, event=None) -> None:
        self._update_visible_items()
    
    def _on_scrollbar(self, *args) -> None:
        self._scrollbar.set(*args)
        self._update_visible_items()
    
    def _update_visible_items(self) -> None:
        if not self.items or not self.create_item_func:
            return
        
        viewport_height = self.winfo_height()
        if viewport_height <= 1:
            viewport_height = 600
        
        scroll_position = self._parent_canvas.yview()[0]
        total_height = len(self.items) * self.item_height
        scroll_offset = scroll_position * total_height
        
        first_index = max(0, int(scroll_offset / self.item_height) - self.buffer_size)
        last_index = min(
            len(self.items),
            int((scroll_offset + viewport_height) / self.item_height) + self.buffer_size + 1
        )
        
        if first_index == self.first_visible_index and last_index == self.last_visible_index:
            return
        
        self.first_visible_index = first_index
        self.last_visible_index = last_index
        
        self._clear_visible_widgets()
        
        if first_index > 0:
            spacer_height = first_index * self.item_height
            spacer = ctk.CTkFrame(self, height=spacer_height, fg_color="transparent")
            spacer.pack(fill="x")
            spacer.pack_propagate(False)
            self.visible_widgets['top_spacer'] = spacer
        
        for i in range(first_index, last_index):
            if i < len(self.items):
                item_frame = ctk.CTkFrame(self, height=self.item_height)
                item_frame.pack(fill="x", pady=1)
                item_frame.pack_propagate(False)
                
                self.create_item_func(self.items[i], item_frame)
                self.visible_widgets[f'item_{i}'] = item_frame
        
        remaining_items = len(self.items) - last_index
        if remaining_items > 0:
            spacer_height = remaining_items * self.item_height
            spacer = ctk.CTkFrame(self, height=spacer_height, fg_color="transparent")
            spacer.pack(fill="x")
            spacer.pack_propagate(False)
            self.visible_widgets['bottom_spacer'] = spacer
    
    def _clear_visible_widgets(self) -> None:
        for widget in self.visible_widgets.values():
            widget.destroy()
        self.visible_widgets.clear()
    
    def get_visible_range(self) -> tuple:
        return (self.first_visible_index, self.last_visible_index)
    
    def scroll_to_item(self, index: int) -> None:
        if 0 <= index < len(self.items):
            position = (index * self.item_height) / (len(self.items) * self.item_height)
            self._parent_canvas.yview_moveto(position)
            self._update_visible_items()
