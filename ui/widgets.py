import tkinter as tk
from typing import Optional, Literal, Any
from ui.theme import THEME

def _container_of(phone_frame):
    """Return the content container if present, else the frame itself."""
    return phone_frame.content if hasattr(phone_frame, "content") else phone_frame

def _make_label(
    parent,
    text,
    font=("Helvetica", 18, "bold"),
    wraplength: Optional[int] = None,
    justify: Literal["left", "center", "right"] = "left",
    **kwargs: Any,
):
    """Create a styled tk.Label with common theme settings."""
    return tk.Label(
        parent,
        text=text,
        font=font,
        fg=THEME["text_primary"],
        bg=THEME["card"],
        wraplength=wraplength,
        justify=justify,
        **kwargs,
    )