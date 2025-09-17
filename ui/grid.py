# ui/overlay.py
"""Overlay layer for hover preview images.

show_overlay_from_file(phone_frame, image_path, size=(540, 560))
  - draws a full-size overlay over phone_frame.grid_frame (fallback to content)
  - centers the provided image, resized to the given size

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
except Exception:
    _BG = "#111827"


def _parent_for_overlay(phone_frame) -> tk.Widget:
    # Prefer the grid frame to align exactly over the tiles; fallback to content/phone_frame
    grid = getattr(phone_frame, "grid_frame", None)
    if isinstance(grid, tk.Widget):
        return grid
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


def show_overlay_from_file(phone_frame, image_path: str, size: Tuple[int, int] = (540, 560)) -> None:
    """Render a full-size overlay over the grid area with the provided image path."""
    parent = _parent_for_overlay(phone_frame)

    # Create overlay frame if missing
    overlay: Optional[tk.Frame] = getattr(phone_frame, "_overlay_frame", None)
    if overlay is None or not isinstance(overlay, tk.Frame) or overlay.master is not parent:
        overlay = tk.Frame(parent, bg=_BG)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        setattr(phone_frame, "_overlay_frame", overlay)

    # Image label inside overlay
    img_label: Optional[tk.Label] = getattr(phone_frame, "_overlay_image_label", None)
    if img_label is None or not isinstance(img_label, tk.Label) or img_label.master is not overlay:
        img_label = tk.Label(overlay, bd=0, highlightthickness=0, bg=_BG)
        setattr(phone_frame, "_overlay_image_label", img_label)
        img_label.place(relx=0.5, rely=0.5, anchor="center")

    # Load and resize the image to exactly the grid size (may stretch to fit)
    try:
        pil_img = PILImage.open(image_path).convert("RGBA").resize(size, PILImage.Resampling.LANCZOS)
        tk_img = PILImageTk.PhotoImage(pil_img)
        img_label.config(image=tk_img)
        _attach_image_ref(img_label, tk_img)
    except Exception:
        # On failure, hide any existing overlay to avoid a blank panel
        hide_overlay(phone_frame)
        return

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


"""Grid rendering and click handlers."""
import os
import tkinter as tk
from PIL import Image, ImageTk
from settings import SETTINGS

from ui.theme import THEME
from ui.images import _add_rounded_corners, _make_border_overlay
from ui.descriptions import _description_for
from ui.text import _update_labels, set_text_if, end_round, HEADER_WIN, HEADER_LOSE
from ui.widgets import _make_label, _container_of
from ui.sounds import play_chime, play_error
from ui.overlay import show_overlay_from_file, hide_overlay

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
    phone_frame.grid_frame = grid_frame

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

        # Store original image path for overlay use
        try:
            tile._image_path = os.path.join(SETTINGS.PATHS.IMAGES, image_file)
        except Exception:
            tile._image_path = None

        # Hover behaviour
        try:
            def _on_enter(_e, wf=grid_frame, ww=tile):
                setattr(ww, "_hovering", True)
                _schedule_hover_preview(wf, ww)
            def _on_leave(_e, wf=grid_frame, ww=tile):
                _cancel_hover_preview(wf, ww)
                if getattr(wf, "_overlay_active", False):
                    try:
                        hide_overlay(wf)
                    except Exception:
                        pass
                    finally:
                        wf._overlay_active = False
            tile.bind("<Enter>", _on_enter)
            tile.bind("<Leave>", _on_leave)
        except Exception:
            pass

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


HOVER_PREVIEW_DELAY_MS = 3000  # 3 seconds


def _schedule_hover_preview(phone_frame, widget):
    try:
        # Cancel any prior timer
        timer_id = getattr(widget, "_hover_timer_id", None)
        if timer_id is not None:
            try:
                phone_frame.after_cancel(timer_id)
            except Exception:
                pass
        # Schedule new
        def _fire():
            if getattr(widget, "_hovering", False):
                image_path = getattr(widget, "_image_path", None)
                if image_path:
                    show_overlay_from_file(phone_frame, image_path, size=(540, 560))
                    phone_frame._overlay_active = True
                    # Bind motion on the grid area to dismiss
                    grid = getattr(phone_frame, "grid_frame", None) or getattr(phone_frame, "content", phone_frame)
                    try:
                        setattr(grid, "_phone_frame", phone_frame)
                        grid.bind("<Motion>", _dismiss_overlay_on_motion)
                    except Exception:
                        pass
        widget._hover_timer_id = phone_frame.after(HOVER_PREVIEW_DELAY_MS, _fire)
    except Exception:
        pass


def _cancel_hover_preview(phone_frame, widget):
    try:
        setattr(widget, "_hovering", False)
        timer_id = getattr(widget, "_hover_timer_id", None)
        if timer_id is not None:
            try:
                phone_frame.after_cancel(timer_id)
            except Exception:
                pass
            finally:
                widget._hover_timer_id = None
    except Exception:
        pass


def _dismiss_overlay_on_motion(event):
    phone_frame = getattr(event.widget, "_phone_frame", None) or getattr(event.widget.master, "_phone_frame", None)
    if phone_frame is None:
        return
    if getattr(phone_frame, "_overlay_active", False):
        try:
            hide_overlay(phone_frame)
        except Exception:
            pass
        finally:
            phone_frame._overlay_active = False
            try:
                grid = getattr(phone_frame, "grid_frame", None) or getattr(phone_frame, "content", phone_frame)
                grid.unbind("<Motion>")
            except Exception:
                pass


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