# ===== FILE: components/CustomScrollbar.py =====
from tkinter import ttk

class CustomScrollbar:
    """Utility class để setup custom scrollbar style"""
    
    @staticmethod
    def setup_style():
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure(
            "Custom.Vertical.TScrollbar",
            background="#E0E0E0",
            troughcolor="#F9F8F8",
            borderwidth=0,
            arrowsize=0,
            width=8
        )
        
        style.map(
            "Custom.Vertical.TScrollbar",
            background=[
                ("active", "#B0B0B0"),
                ("!active", "#E0E0E0")
            ]
        )

