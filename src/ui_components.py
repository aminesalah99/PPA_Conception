
"""
UI Components Module

This module contains reusable UI components used throughout the application.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from PIL import Image, ImageTk, ImageOps
from typing import Dict, Tuple, Set, Optional, List
from functools import lru_cache
from threading import Timer

class UIComponent:
    """A reusable UI component wrapper that creates a labeled frame."""
    def __init__(self, parent, text, command=None):
        self.frame = tk.LabelFrame(parent, text=text, padx=5, pady=5)
        self.command = command

class CanvasManager:
    """Manages the canvas where teeth and dental saddles are displayed."""
    def __init__(self, parent, width=800, height=600):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.width = width
        self.height = height
        self.bg_id = None
        self.bg_photo = None
        self.bg_scale_factor = 1.0
        self.bg_width = 0
        self.bg_height = 0
        self.original_bg_width = 0
        self.original_bg_height = 0

    def bind_resize(self, callback):
        """Bind a callback function to canvas resize events."""
        self.canvas.bind("<Configure>", callback)

    def create_image(self, x, y, image, tags, anchor=tk.CENTER):
        """Create an image on the canvas."""
        return self.canvas.create_image(x, y, image=image, tags=tags, anchor=anchor)

    def delete(self, item):
        """Delete an item from the canvas."""
        self.canvas.delete(item)

    def coords(self, item):
        """Get the coordinates of an item on the canvas."""
        return self.canvas.coords(item)

    def set_coords(self, item, x, y):
        """Set the coordinates of an item on the canvas."""
        self.canvas.coords(item, x, y)

    def tag_raise(self, tag):
        """Raise items with a given tag to the top."""
        self.canvas.tag_raise(tag)

    def tag_lower(self, tag):
        """Lower items with a given tag to the bottom."""
        self.canvas.tag_lower(tag)

    def tag_bind(self, tag, event, callback):
        """Bind a callback to items with a given tag."""
        self.canvas.tag_bind(tag, event, callback)
