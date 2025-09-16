"""Layout-related UI (window + top sections).
This module defines the window and top-of-card instruction/chances area.
It must NOT contain game launcher/round selection logic to avoid circular imports.
"""
import tkinter as tk
from .theme import THEME
from .text import _instruction_text, _chances_text
from .widgets import _container_of, _make_label

__all__ = [
    "setup_main_window",
    "create_phone_frame",
    "create_instruction_label",
]


def setup_main_window():
    root = tk.Tk()
    root.title("Mobile Phone Simulation")
    root.geometry("600x1000")  # Window size
    root.resizable(False, False)
    root.configure(bg=THEME["bg"])  # modern dark background
    return root


def create_phone_frame(root):
    """Creates the phone frame (modern card layout with header/footer)."""
    phone_frame = tk.Frame(root, bg=THEME["surface"], width=600, height=1000)
    phone_frame.pack_propagate(False)
    phone_frame.pack()

    # Content container (card)
    content = tk.Frame(phone_frame, bg=THEME["card"], width=560, height=820, highlightthickness=1)
    content.configure(highlightbackground=THEME["card_border"], highlightcolor=THEME["card_border"])
    content.pack(padx=20, pady=(0, 12))
    content.pack_propagate(False)
    phone_frame.content = content  # store for other builders

    # Footer bar (sticky controls)
    footer = tk.Frame(phone_frame, bg=THEME["surface"], height=120)
    footer.pack(fill=tk.X, side=tk.BOTTOM)
    phone_frame.footer = footer

    # --- Footer content: message (top) + buttons (bottom) ---
    footer_content = tk.Frame(footer, bg=THEME["surface"])
    footer_content.pack(side=tk.TOP, fill=tk.X, pady=(0, 20))  # buttons 20px off bottom

    footer_msg = tk.Label(
        footer_content,
        text="",
        font=("Helvetica", 18, "bold"),  # match instruction font
        fg=THEME["text_muted"],
        bg=THEME["surface"],
        anchor="center",
    )
    footer_msg.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))

    buttons_frame = tk.Frame(footer_content, bg=THEME["surface"])
    buttons_frame.pack(side=tk.TOP)

    def _exit_app():
        phone_frame.winfo_toplevel().destroy()

    play_again_btn = tk.Button(
        buttons_frame,
        text="Play again",
        state="disabled",  # only enabled at end-of-round
        relief=tk.RIDGE,
        cursor="arrow",
        command=lambda: getattr(phone_frame, "on_play_again", (lambda: None))(),
    )
    play_again_btn.pack(side=tk.LEFT, padx=(6, 12))

    exit_btn = tk.Button(
        buttons_frame,
        text="Exit",
        relief=tk.RIDGE,
        command=_exit_app,
    )
    exit_btn.pack(side=tk.LEFT, padx=(12, 6))

    # Save references for other modules
    phone_frame.footer_msg = footer_msg
    phone_frame.play_again_btn = play_again_btn
    phone_frame.exit_btn = exit_btn
    phone_frame.round_over = False

    return phone_frame


def create_instruction_label(phone_frame, random_letter, num_images_to_find):
    """Creates and displays the instruction label (modern heading + chances)."""
    container = _container_of(phone_frame)
    wrap = tk.Frame(container, bg=THEME["card"])
    wrap.pack(fill=tk.X, padx=20, pady=(20, 8))

    # Instruction heading
    instruction_text = _instruction_text(num_images_to_find, random_letter, num_images_to_find)
    msg = _make_label(
        wrap,
        text=instruction_text,
        font=("Helvetica", 18, "bold"),
        wraplength=500,
        justify="left",
        anchor="center",
    )
    msg.pack(fill=tk.X, pady=(0, 4))

    # Store references so we can update later
    phone_frame.instruction_msg = msg
    phone_frame.num_images_to_find = num_images_to_find
    phone_frame.initial_num_images_to_find = num_images_to_find
    phone_frame.random_letter = random_letter

    # Chances line (beneath instruction)
    chances_label = _make_label(
        wrap,
        text=_chances_text(num_images_to_find + 1, num_images_to_find + 1),
        font=("Helvetica", 18, "bold"),
        justify="left",
        anchor="center",
    )
    chances_label.pack(fill=tk.X)

    # Store chances label and counters for later updates
    phone_frame.chances_label = chances_label
    phone_frame.chances_remaining = num_images_to_find + 1
    phone_frame.initial_chances = num_images_to_find + 1