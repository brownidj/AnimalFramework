# game/rounds.py
"""Round construction utilities (decoupled from UI)."""

from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set


@dataclass(frozen=True)
class RoundState:
    letter: str
    selected: List[str]  # filenames only
    correct: Set[str]  # subset of selected (filenames)


def _files_in(images_folder: str | os.PathLike[str]) -> List[str]:
    """Return sorted PNG filenames in the folder (filenames only)."""
    folder = Path(images_folder)
    return sorted([p.name for p in folder.glob("*.png")])


def choose_round(
        rng: random.Random,
        images_folder: str | os.PathLike[str],
        k: int,
        min_correct: int = 2,
        max_correct: int = 5,
        max_attempts: int = 200,
) -> RoundState:
    """Compose a round with exactly *k* images.

    Picks a random *letter* that exists among filenames, then a random number of
    correct picks in [min_correct, max_correct]. Fills the remainder with non-matching files.
    Returns a RoundState.
    """
    all_files = _files_in(images_folder)
    if len(all_files) < k:
        raise RuntimeError(f"Need at least {k} PNGs in '{images_folder}', found {len(all_files)}.")

    stems = [Path(f).stem for f in all_files if Path(f).stem]
    letters_present = sorted({s[0].upper() for s in stems})
    if not letters_present:
        raise RuntimeError("No valid stems to choose a letter from.")

    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        letter = rng.choice(letters_present)
        target_correct = rng.randint(min_correct, max_correct)

        matches = [f for f in all_files if Path(f).stem.lower().startswith(letter.lower())]
        nonmatches = [f for f in all_files if f not in matches]

        if len(matches) < target_correct or len(nonmatches) < (k - target_correct):
            continue

        correct_sel = rng.sample(matches, target_correct)
        distractors = rng.sample(nonmatches, k - target_correct)
        selected = correct_sel + distractors
        rng.shuffle(selected)
        return RoundState(letter=letter, selected=selected, correct=set(correct_sel))

    raise RuntimeError(
        "Could not build a round that meets the constraints after several attempts. "
        "Add more images or adjust constraints."
    )
