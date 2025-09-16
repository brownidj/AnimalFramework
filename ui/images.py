from PIL import Image as PILImage, ImageDraw as PILDraw

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