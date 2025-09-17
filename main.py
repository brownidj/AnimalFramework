"""Launcher for the AnimalFramework UI.
Build a 3×3 grid (9 tiles) where a random letter is chosen.
The number of correct tiles (beginning with that letter) is a random int in [2, 5].
The remaining tiles are randomly chosen from images that do NOT begin with that letter.
"""
import random

from settings import SETTINGS
from game import choose_round, RoundState
from ui import (
    setup_main_window,
    create_phone_frame,
    create_instruction_label,
    create_grid_frame,
    display_images,
    resize_images,
)
from ui.sounds import reset_chime_counter
from ui.helpers import set_text, enable, clear_description



def clear_content_area(phone):
    """Remove all children from phone.content and release any image references."""
    content = getattr(phone, "content", None)
    if content is None:
        return

    for child in list(content.winfo_children()):
        # Explicitly drop image references if present
        if hasattr(child, "image"):
            child.image = None
        if hasattr(child, "images"):
            try:
                child.images.clear()
            except Exception:
                # Fallback: overwrite with empty list if it's not a mutable sequence
                child.images = []
        child.destroy()


def start_round(phone, rng):
    """Reset UI and start a fresh round."""
    # Clear prior content (grid + headers inside the content card)
    clear_content_area(phone)

    set_text(getattr(phone, "footer_msg", None), "")
    enable(getattr(phone, "play_again_btn", None), False)
    setattr(phone, "round_over", False)
    clear_description(getattr(phone, "description_var", None))

    # Reset chime sequence
    reset_chime_counter()

    # Choose round and render
    state: RoundState = choose_round(
        rng,
        SETTINGS.PATHS.IMAGES,
        SETTINGS.GRID.GRID_COUNT,
        SETTINGS.RULES.MIN_CORRECT,
        SETTINGS.RULES.MAX_CORRECT,
    )

    num_images_to_find = len(state.correct)
    create_instruction_label(phone, state.letter, num_images_to_find)
    grid = create_grid_frame(phone)

    tk_images = resize_images(SETTINGS.PATHS.IMAGES, state.selected)
    display_images(grid, tk_images, state.correct, state.letter)

def main():
    rng = random.Random(SETTINGS.DEBUG.RANDOM_SEED) if SETTINGS.DEBUG.RANDOM_SEED is not None else random.Random()

    root = setup_main_window()
    phone = create_phone_frame(root)

    # Wire the Play again button (created by layout) to restart the round
    phone.on_play_again = lambda: start_round(phone, rng)

    # First round
    start_round(phone, rng)
    root.mainloop()


if __name__ == "__main__":
    main()
