# ui/overlay.py
"""Overlay layer for hover preview images.

show_overlay_from_file(phone_frame, image_path, size=(540, 560))
  - draws an overlay over the grid/content area
  - loads the image from disk and resizes to the given size

show_overlay(phone_frame, photoimage)
  - legacy helper if a Tk PhotoImage is already available

hide_overlay(phone_frame)
  - removes the overlay if present
"""
from __future__ import annotations
import tkinter as tk
from typing import Optional, Tuple
from PIL import Image as PILImage, ImageTk as PILImageTk

try:
    from settings import SETTINGS  # theme colours
    _BG = getattr(SETTINGS.THEME, "SURFACE", "#111827")
    _RADIUS = getattr(SETTINGS.GRID, "TILE_RADIUS", 24)
    _BORDER_COLOR = getattr(SETTINGS.THEME, "TILE_BORDER", "#334155")
    _BORDER_WIDTH = getattr(SETTINGS.GRID, "OUTLINE_WIDTH", 4)
except Exception:
    _BG = "#111827"
    _RADIUS = 24
    _BORDER_COLOR = "#334155"
    _BORDER_WIDTH = 4


def _parent_for_overlay(phone_frame) -> tk.Widget:
    # Prefer a grid_frame if the layout code has set one; else fall back to content/phone_frame
    parent = getattr(phone_frame, "grid_frame", None)
    if isinstance(parent, tk.Widget):
        return parent
    return getattr(phone_frame, "content", phone_frame)


def _attach_image_ref(widget: tk.Widget, img) -> None:
    """Ensure widget keeps strong refs to Tk PhotoImage(s)."""
    try:
        if not hasattr(widget, "image") or widget.image is None:
            widget.image = img
        if not hasattr(widget, "images") or widget.images is None:
            widget.images = []
        if img not in widget.images:
            widget.images.append(img)
    except Exception:
        pass


def _ensure_overlay_widgets(phone_frame) -> tuple[tk.Frame, tk.Label]:
    parent = _parent_for_overlay(phone_frame)

    overlay: Optional[tk.Frame] = getattr(phone_frame, "_overlay_frame", None)
    if overlay is None or not isinstance(overlay, tk.Frame) or overlay.master is not parent:
        overlay = tk.Frame(parent, bg=_BG)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        setattr(phone_frame, "_overlay_frame", overlay)

    img_label: Optional[tk.Label] = getattr(phone_frame, "_overlay_image_label", None)
    if img_label is None or not isinstance(img_label, tk.Label) or img_label.master is not overlay:
        img_label = tk.Label(overlay, bd=0, highlightthickness=0, bg=_BG)
        setattr(phone_frame, "_overlay_image_label", img_label)
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        def _overlay_click(_e, pf=phone_frame):
            # Hide overlay first
            try:
                hide_overlay(pf)
            except Exception:
                pass
            try:
                setattr(pf, "_overlay_active", False)
            except Exception:
                pass
            # Unbind motion listener if any
            try:
                grid = getattr(pf, "grid_frame", None) or getattr(pf, "content", pf)
                grid.unbind("<Motion>")
            except Exception:
                pass
            # Forward the click to the original tile widget
            src = getattr(pf, "_overlay_source_widget", None)
            if src is not None:
                try:
                    src.event_generate("<Button-1>")
                except Exception:
                    pass
            # Clear the source pointer
            try:
                setattr(pf, "_overlay_source_widget", None)
            except Exception:
                pass

        img_label.bind("<Button-1>", _overlay_click)

    return overlay, img_label


def _hex_to_rgba(hex_color: str, alpha: int = 255):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def show_overlay_from_file(phone_frame, image_path: str, size: Tuple[int, int] = (540, 560)) -> None:
    """Render an overlay using an image from disk resized to `size` (default 540x560)."""
    overlay, img_label = _ensure_overlay_widgets(phone_frame)

    # Load and resize the image to exactly the requested size, and apply rounded corners and a border
    try:
        from PIL import ImageDraw as PILDraw

        # Base background matching the overlay panel so transparent corners are visible
        bg = PILImage.new("RGBA", size, _hex_to_rgba(_BG, 255))

        # Resize the source to EXACT size (per spec). If you prefer aspect-preserving, switch to thumbnail.
        src = PILImage.open(image_path).convert("RGBA").resize(size, PILImage.Resampling.LANCZOS)

        # Rounded mask
        mask = PILImage.new("L", size, 0)
        draw = PILDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, size[0], size[1]], radius=int(_RADIUS), fill=255)

        # Composite: paste src onto bg using rounded mask
        bg.paste(src, (0, 0), mask)

        # Draw a rounded border on top so the rounding is unmistakable
        bdraw = PILDraw.Draw(bg)
        inset = max(1, _BORDER_WIDTH // 2 + 2)
        x1, y1 = inset, inset
        x2, y2 = size[0] - inset - 1, size[1] - inset - 1
        try:
            bdraw.rounded_rectangle([x1, y1, x2, y2], radius=max(1, int(_RADIUS) - 3), outline=_BORDER_COLOR, width=int(_BORDER_WIDTH))
        except Exception:
            bdraw.rectangle([x1, y1, x2, y2], outline=_BORDER_COLOR, width=int(_BORDER_WIDTH))

        tk_img = PILImageTk.PhotoImage(bg)
        img_label.config(image=tk_img)
        _attach_image_ref(img_label, tk_img)
    except Exception:
        hide_overlay(phone_frame)
        return

    try:
        overlay.lift()
    except Exception:
        pass

    setattr(phone_frame, "_overlay_active", True)


def show_overlay(phone_frame, photoimage) -> None:
    """Legacy: render an overlay using an existing Tk PhotoImage (already sized)."""
    overlay, img_label = _ensure_overlay_widgets(phone_frame)
    try:
        img_label.config(image=photoimage)
        _attach_image_ref(img_label, photoimage)
    except Exception:
        pass

    def _overlay_click(_e, pf=phone_frame):
        try:
            hide_overlay(pf)
        except Exception:
            pass
        try:
            setattr(pf, "_overlay_active", False)
        except Exception:
            pass
        try:
            grid = getattr(pf, "grid_frame", None) or getattr(pf, "content", pf)
            grid.unbind("<Motion>")
        except Exception:
            pass
        src = getattr(pf, "_overlay_source_widget", None)
        if src is not None:
            try:
                src.event_generate("<Button-1>")
            except Exception:
                pass
        try:
            setattr(pf, "_overlay_source_widget", None)
        except Exception:
            pass

    img_label.bind("<Button-1>", _overlay_click)

    try:
        overlay.lift()
    except Exception:
        pass
    setattr(phone_frame, "_overlay_active", True)


def hide_overlay(phone_frame) -> None:
    """Remove overlay elements if present and clear flags."""
    overlay: Optional[tk.Frame] = getattr(phone_frame, "_overlay_frame", None)
    img_label: Optional[tk.Label] = getattr(phone_frame, "_overlay_image_label", None)

    try:
        if img_label is not None:
            img_label.place_forget()
            img_label.destroy()
    except Exception:
        pass

    try:
        if overlay is not None:
            overlay.place_forget()
            overlay.destroy()
    except Exception:
        pass

    try:
        setattr(phone_frame, "_overlay_image_label", None)
        setattr(phone_frame, "_overlay_frame", None)
        setattr(phone_frame, "_overlay_active", False)
    except Exception:
        pass