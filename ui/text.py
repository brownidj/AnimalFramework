from typing import Optional

# --- Minimal pluralisation + formatters ---

def _pluralize(n: int, singular: str, plural: Optional[str] = None) -> str:
    """Return the correctly pluralized word for n (1 -> singular, else plural)."""
    return singular if n == 1 else (plural or f"{singular}s")

def _instruction_text(remaining: int, letter: str, initial: int) -> str:
    more = " more" if remaining < initial else ""
    return f"Find {remaining}{more} {_pluralize(remaining, 'animal')} beginning with {letter}"

def _chances_text(remaining: int, initial: int) -> str:
    more = " more" if remaining < initial else ""
    return f"You have {remaining}{more} {_pluralize(remaining, 'chance')}"

def _update_labels(phone_frame) -> None:
    """Re-render instruction and chances labels from state on phone_frame."""
    if hasattr(phone_frame, 'instruction_msg'):
        phone_frame.instruction_msg.config(
            text=_instruction_text(
                getattr(phone_frame, 'num_images_to_find', 0),
                getattr(phone_frame, 'random_letter', ''),
                getattr(phone_frame, 'initial_num_images_to_find', 0),
            )
        )
    if hasattr(phone_frame, 'chances_label'):
        phone_frame.chances_label.config(
            text=_chances_text(
                getattr(phone_frame, 'chances_remaining', 0),
                getattr(phone_frame, 'initial_chances', 0),
            )
        )

# --- Shared UI text (centralised) ---

NOT_ENOUGH_CHANCES = "Not enough chances left to find all the animals"

# Shared headers and footer
HEADER_WIN = "Congratulations!"
HEADER_LOSE = "Commiserations! Game over"
FOOTER_TAP = "Click on any animal to see the name and a description"


def set_text_if(widget, text):
    """Safely set text on a Tk widget with .config(text=...)."""
    if widget is not None:
        try:
            widget.config(text=text)
        except Exception:
            pass


def end_round(phone_frame, header_text: str, sublabel_text: str):
    """Common end-of-round UI updates and flags."""
    instruction = getattr(phone_frame, "instruction_msg", None)
    set_text_if(instruction, header_text)

    chances_label = getattr(phone_frame, "chances_label", None)
    set_text_if(chances_label, sublabel_text)

    footer = getattr(phone_frame, "footer_msg", None)
    set_text_if(footer, FOOTER_TAP)

    play_again = getattr(phone_frame, "play_again_btn", None)
    if play_again is not None:
        try:
            play_again.config(state="normal", cursor="hand2")
        except Exception:
            pass

    phone_frame.round_over = True


def win_sublabel_all(total: Optional[int]) -> str:
    """Return 'You found all X animals!' (or a generic variant)."""
    if isinstance(total, int) and total > 0:
        return f"You found all {total} animals!"
    return "You found all animals!"


def lose_sublabel_found_of_total(found: int, total: int) -> str:
    """Return 'You found N out of M animals'."""
    return f"You found {found} out of {total} animals"


def round_ended_text() -> str:
    return "Round ended"


def score_text(score: int) -> str:
    return f"You scored {score} points"