"""Grid rendering and click handlers."""
import os
import tkinter as tk
from PIL import Image, ImageTk

from ui.theme import THEME
from ui.images import _add_rounded_corners, _make_border_overlay
from ui.descriptions import _description_for
from ui.text import _update_labels, set_text_if, end_round, HEADER_WIN, HEADER_LOSE
from ui.widgets import _make_label, _container_of
from ui.sounds import play_chime, play_error

__all__ = [
    "resize_images",
    "create_grid_frame",
    "display_images",
    "evaluate_image_click_canvas",
    "evaluate_image_click_composite",
]


def create_grid_frame(phone_frame):
    """Creates the frame that will contain the 3x3 grid (inside card)."""
    container = _container_of(phone_frame)
    grid_frame = tk.Frame(container, bg=THEME["card"], width=540, height=560)
    grid_frame.pack_propagate(False)
    grid_frame.pack(padx=10, pady=(0, 10))

    # Description area below the grid
    desc_var = tk.StringVar(value="")
    desc_label = _make_label(
        container,
        text="",
        font=("Helvetica", 13),
        wraplength=520,
        justify="left",
        anchor="w",
        padx=14,
        pady=10,
        textvariable=desc_var,
    )
    desc_label.pack(fill=tk.X, padx=10, pady=(0, 12))

    # attach to grid_frame so click handler can update it
    grid_frame.description_var = desc_var
    grid_frame.description_label = desc_label
    phone_frame.description_var = desc_var

    return grid_frame


def resize_images(images_folder, selected_images):
    """Resizes images to fit the grid, adds rounded corners, converts to Tk images.

    Args:
        images_folder: base folder path containing PNGs
        selected_images: list of image filenames (strings)

    Returns:
        List[Tuple[str, ImageTk.PhotoImage]] of (filename, tk_image)
    """
    resized_images = []
    for image_file in selected_images:
        img_path = os.path.join(images_folder, image_file)
        img = Image.open(img_path).convert("RGBA")
        img = img.resize((160, 160), Image.Resampling.LANCZOS)
        img = _add_rounded_corners(img, radius=24)
        resized_images.append((image_file, ImageTk.PhotoImage(img)))
    return resized_images


def display_images(grid_frame, resized_images, correct_images, random_letter):
    """Displays images in a 3x3 grid with tappable modern tiles."""
    for idx, (image_file, tk_image) in enumerate(resized_images):
        tile = tk.Canvas(
            grid_frame,
            width=160,
            height=160,
            bg=THEME["card"],
            highlightthickness=0,
            borderwidth=0,
            cursor="hand2",
        )
        tile.grid(row=idx // 3, column=idx % 3, padx=6, pady=6)

        # Base image (already rounded in resize_images)
        tile.create_image(0, 0, image=tk_image, anchor="nw")

        # Pre-build overlay images for positive/negative states (rounded outline, transparent centre)
        pos_overlay_img = _make_border_overlay(size=(160, 160), radius=21, color=THEME["positive"], width=4)
        neg_overlay_img = _make_border_overlay(size=(160, 160), radius=21, color=THEME["negative"], width=4)

        pos_overlay_tk = ImageTk.PhotoImage(pos_overlay_img)
        neg_overlay_tk = ImageTk.PhotoImage(neg_overlay_img)

        overlay_item = tile.create_image(0, 0, image=neg_overlay_tk, anchor="nw", state="hidden")

        # Keep references to avoid GC
        tile._base_image = tk_image
        tile._pos_overlay_tk = pos_overlay_tk
        tile._neg_overlay_tk = neg_overlay_tk
        tile._overlay_item = overlay_item

        tile.bind(
            "<Button-1>",
            lambda event, file=image_file, canvas=tile: evaluate_image_click_composite(file, canvas, correct_images, random_letter),
        )

    grid_frame.image_references = [img[1] for img in resized_images]


def evaluate_image_click_canvas(image_file, canvas, rect_id, correct_images, random_letter):
    """Legacy handler (kept for compatibility); prefer the composite overlay version."""
    import os as _os
    is_correct = _os.path.basename(image_file) in correct_images
    color = THEME["positive"] if is_correct else THEME["negative"]
    canvas.itemconfigure(rect_id, state="normal", outline=color, fill="")

    def _pulse(step=0):
        width = 5 if (step % 2 == 0) else 3
        canvas.itemconfigure(rect_id, width=width)
        if step < 3:
            canvas.after(90, _pulse, step + 1)
        else:
            canvas.itemconfigure(rect_id, width=3, fill="")
    _pulse()

    parent_grid = canvas.master
    if hasattr(parent_grid, "description_var"):
        parent_grid.description_var.set(_description_for(image_file))


def _show_overlay_with_pulse(canvas, is_correct: bool):
    overlay_img = canvas._pos_overlay_tk if is_correct else canvas._neg_overlay_tk
    canvas.itemconfigure(canvas._overlay_item, image=overlay_img, state="normal")

    def _pulse(step=0):
        if step == 0:
            color = THEME["positive"] if is_correct else THEME["negative"]
            pulse_overlay = _make_border_overlay(size=(160, 160), radius=21, color=color, width=4)
            canvas._pulse_overlay_tk = ImageTk.PhotoImage(pulse_overlay)
            canvas.itemconfigure(canvas._overlay_item, image=canvas._pulse_overlay_tk)
            canvas.after(90, _pulse, 1)
        else:
            canvas.itemconfigure(canvas._overlay_item, image=overlay_img)
    _pulse()


def _get_phone_frame_from_canvas(canvas):
    # Walk up the widget tree until we find the frame that owns the round state
    node = canvas
    for _ in range(6):  # safety bound
        if node is None:
            return None
        if (
            hasattr(node, "num_images_to_find")
            or hasattr(node, "chances_remaining")
            or hasattr(node, "instruction_msg")
            or hasattr(node, "chances_label")
        ):
            return node
        node = getattr(node, "master", None)
    return None


def _apply_click_effects_and_counters(phone_frame, is_correct: bool):
    # Decrement counters
    if hasattr(phone_frame, "chances_remaining") and phone_frame.chances_remaining > 0:
        phone_frame.chances_remaining -= 1
    if is_correct and hasattr(phone_frame, "num_images_to_find") and phone_frame.num_images_to_find > 0:
        phone_frame.num_images_to_find -= 1
    # Refresh labels
    _update_labels(phone_frame)


def _maybe_end_round(phone_frame):
    has_targets = hasattr(phone_frame, "num_images_to_find")
    has_chances = hasattr(phone_frame, "chances_remaining")
    if not (has_targets and has_chances):
        return

    # Win condition
    if phone_frame.num_images_to_find == 0:
        total = getattr(phone_frame, "initial_num_images_to_find", None)
        if isinstance(total, int) and total > 0:
            sub = f"You found all {total} animals!"
        else:
            sub = "You found all animals!"
        end_round(phone_frame, HEADER_WIN, sub)
        return

    # Insufficient chances to finish: end round early
    if (
        phone_frame.num_images_to_find > 0 and
        phone_frame.chances_remaining >= 0 and
        phone_frame.num_images_to_find > phone_frame.chances_remaining
    ):
        remaining = getattr(phone_frame, "num_images_to_find", 0)
        end_round(phone_frame, HEADER_LOSE, f"Too few chances to find the remaining {remaining} animals")
        return

    # Lose condition (no chances left)
    if phone_frame.chances_remaining == 0:
        total = getattr(phone_frame, "initial_num_images_to_find", None)
        if isinstance(total, int) and total >= 0:
            found = total - max(getattr(phone_frame, "num_images_to_find", 0), 0)
            sub = f"You found {found} out of {total} animals"
        else:
            sub = "Round ended"
        end_round(phone_frame, HEADER_LOSE, sub)


def evaluate_image_click_composite(image_file, canvas, correct_images, random_letter):
    """Click handler for composite image tiles: toggle a prebuilt PNG overlay with rounded border."""
    import os as _os
    is_correct = _os.path.basename(image_file) in correct_images

    # 1) Visual feedback
    _show_overlay_with_pulse(canvas, is_correct)

    # 2) Update description text (below grid)
    parent_grid = canvas.master
    if hasattr(parent_grid, "description_var"):
        parent_grid.description_var.set(_description_for(image_file))

    # 3) Counters + labels on the phone frame
    phone_frame = _get_phone_frame_from_canvas(canvas)
    if not phone_frame:
        return

    # Play a soft chime or error for clicks during an active round
    if not getattr(phone_frame, "round_over", False):
        try:
            if is_correct:
                play_chime()
            else:
                play_error()
        except Exception:
            pass

    # If the round has ended, allow description updates but do not change counters/labels
    if getattr(phone_frame, "round_over", False):
        return

    try:
        _apply_click_effects_and_counters(phone_frame, is_correct)
        _maybe_end_round(phone_frame)
    except Exception:
        pass