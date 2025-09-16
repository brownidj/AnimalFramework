import tkinter as tk
from PIL import Image, ImageTk
import os

import paths

# ===== Modern UI Theme =====
THEME = {
    "bg": "#0f172a",              # slate-900
    "surface": "#111827",         # gray-900
    "card": "#1f2937",            # gray-800
    "card_border": "#374151",     # gray-700
    "tile_border": "#334155",     # slate-700
    "positive": "#22c55e",        # green-500
    "negative": "#9ca3af",        # gray-400
    "accent": "#06b6d4",          # cyan-500
    "text_primary": "#e5e7eb",    # gray-200
    "text_muted": "#9ca3af",      # gray-400
}

def _add_rounded_corners(img, radius=24):
    """Return a copy of PIL.Image with rounded corners (RGBA)."""
    from PIL import Image, ImageDraw
    img = img.convert("RGBA")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, w, h], radius=radius, fill=255)
    img.putalpha(mask)
    return img


    # Keep references to prevent garbage collection
    grid_frame.image_references = [img[1] for img in resized_images]

def evaluate_image_click(image_file, img_label, correct_images, random_letter):
    is_correct = os.path.basename(image_file) in correct_images
    color = THEME["positive"] if is_correct else THEME["negative"]
    img_label.configure(highlightbackground=color, highlightcolor=color)

    # Simple tap animation: briefly thicken border
    def _pulse(step=0):
        thickness = 3 + (2 if step % 2 == 0 else 0)
        img_label.configure(highlightthickness=thickness)
        if step < 3:
            img_label.after(90, _pulse, step + 1)
        else:
            img_label.configure(highlightthickness=3)

    _pulse()


# ===== Utility function to list animal images in assets =====
def list_animals_in_assets():
    """
    Return a list of all animal names based on the PNG files
    found in the assets/images directory.
    """
    images_dir = paths.IMAGES_DIR
    if not os.path.isdir(images_dir):
        return []

    animal_files = [f for f in os.listdir(images_dir) if f.lower().endswith(".png")]
    animal_names = [os.path.splitext(f)[0] for f in animal_files]
    return animal_names


if __name__ == "__main__":
    animals = list_animals_in_assets()
    print("Animals found in assets/images:")
    print(animals)
