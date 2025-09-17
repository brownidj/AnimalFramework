from PIL import Image as PILImage, ImageDraw as PILDraw
from PIL import ImageTk as PILImageTk

# --- Internal: prevent Tk PhotoImage from being GC'd by pinning refs on the widget

def _attach_image_ref(widget, img):
    """Ensure the Tk widget holds strong references to its PhotoImage(s).
    This avoids images disappearing due to Python GC.
    """
    try:
        if not hasattr(widget, "image") or widget.image is None:
            widget.image = img
        if not hasattr(widget, "images") or widget.images is None:
            widget.images = []
        if img not in widget.images:
            widget.images.append(img)
    except Exception:
        # Never crash UI creation due to attribute errors on custom widgets
        pass

def _add_rounded_corners(img, radius=24):
    """Return a copy of PIL.Image with rounded corners (RGBA)."""
    img = img.convert("RGBA")
    w, h = img.size
    mask = PILImage.new("L", (w, h), 0)
    draw = PILDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    img.putalpha(mask)
    return img

def _make_border_overlay(size=(160, 160), radius=21, color="#22c55e", width=4):
    """Return a transparent RGBA image with a rounded outline (no fill)."""
    w, h = size
    overlay = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = PILDraw.Draw(overlay)
    inset = width // 2 + 2  # keep stroke inside rounded image mask
    x1, y1, x2, y2 = inset, inset, w - inset - 1, h - inset - 1
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=color, width=width)
    return overlay

# --- Public convenience: build a Tk PhotoImage and (optionally) pin it to a widget

def make_tk_image(pil_image, *, attach_to_widget=None):
    """Return an ImageTk.PhotoImage built from `pil_image`.
    If `attach_to_widget` is provided, the resulting PhotoImage is pinned on that widget
    to prevent garbage collection (image disappearing in Tkinter).
    """
    tk_img = PILImageTk.PhotoImage(pil_image)
    if attach_to_widget is not None:
        _attach_image_ref(attach_to_widget, tk_img)
    return tk_img