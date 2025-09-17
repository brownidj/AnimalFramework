# ui/helpers.py
"""Small, reusable UI helpers for Tk widgets.
Keep widget-poking in one place so business logic stays clean.
"""
from __future__ import annotations
from typing import Any


def set_text(widget: Any, text: str = "") -> None:
    """Safely set text on a Tk widget that supports .config(text=...)."""
    if widget is None:
        return
    try:
        widget.config(text=text)
    except Exception:
        # Non-fatal: ignore widgets without .config or other hiccups
        pass


def enable(btn: Any, on: bool = True) -> None:
    """Enable/disable a button-like widget and set a sane cursor."""
    if btn is None:
        return
    try:
        btn.config(
            state=("normal" if on else "disabled"),
            cursor=("hand2" if on else "arrow"),
        )
    except Exception:
        pass


def clear_description(var: Any) -> None:
    """Clear a tk.StringVar-like object if it supports .set()."""
    if var is None:
        return
    try:
        var.set("")
    except Exception:
        pass


