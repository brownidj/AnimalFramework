# logic/round_controller.py
"""Round lifecycle controller.
Encapsulates win/lose/impossible logic and remaining counters so UI code stays simple.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

__all__ = ["RoundController", "Outcome"]

Outcome = Literal["continue", "win", "lose", "impossible"]


@dataclass
class RoundController:
    """Tracks per-round counters and computes outcome transitions.

    total_to_find: how many correct tiles exist for this round
    total_chances: how many total chances are allowed (usually total_to_find + 1)
    """

    total_to_find: int
    total_chances: int
    remaining_to_find: int
    remaining_chances: int
    over: bool = False

    def __init__(self, total_to_find: int, total_chances: int):
        self.total_to_find = int(total_to_find)
        self.total_chances = int(total_chances)
        self.remaining_to_find = int(total_to_find)
        self.remaining_chances = int(total_chances)
        self.over = False

    # --- event recording ---
    def record_correct(self) -> Outcome:
        if self.over:
            return "continue"
        self.remaining_to_find = max(0, self.remaining_to_find - 1)
        return self._check()

    def record_incorrect(self) -> Outcome:
        if self.over:
            return "continue"
        self.remaining_chances = max(0, self.remaining_chances - 1)
        return self._check()

    # --- evaluation ---
    def _check(self) -> Outcome:
        if self.remaining_to_find <= 0:
            self.over = True
            return "win"
        if self.remaining_chances <= 0:
            self.over = True
            return "lose"
        if self.remaining_to_find > self.remaining_chances:
            self.over = True
            return "impossible"
        return "continue"

    def outcome(self) -> Outcome:
        """Return current outcome without changing state."""
        if self.remaining_to_find <= 0:
            return "win"
        if self.remaining_chances <= 0:
            return "lose"
        if self.remaining_to_find > self.remaining_chances:
            return "impossible"
        return "continue"

    # --- sync helpers (optional) ---
    def sync_from_phone(self, phone_frame) -> None:
        """Synchronise counters from a phone_frame if it exposes the expected attributes."""
        try:
            self.remaining_to_find = int(getattr(phone_frame, "num_images_to_find", self.remaining_to_find))
            self.remaining_chances = int(getattr(phone_frame, "chances_remaining", self.remaining_chances))
        except Exception:
            # Keep previous values if conversion fails
            pass
