"""ui package public API
Re-export helpers and split modules without circular imports.
"""

# Helpers
from .theme import THEME
from .text import _pluralize, _instruction_text, _chances_text, _update_labels
from .images import _add_rounded_corners, _make_border_overlay
from .descriptions import _load_descriptions, _description_for

# Layout (window + instruction area)
from .layout import (
    setup_main_window,
    create_phone_frame,
    create_instruction_label,
)

# Grid (image tiles + handlers)
from .grid import (
    resize_images,
    create_grid_frame,
    display_images,
    evaluate_image_click_canvas,
    evaluate_image_click_composite,
)