"""Typed application settings using dataclasses.
Unified config with UI theme, grid, game rules, paths, and debug flags.
Access via: from settings import SETTINGS
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from paths import ASSETS_DIR, IMAGES_DIR


# --- UI theme (colours, styling) ---
@dataclass(frozen=True)
class UITheme:
    BG: str = "#0f172a"
    SURFACE: str = "#111827"
    CARD: str = "#1f2937"
    CARD_BORDER: str = "#374151"
    TILE_BORDER: str = "#334155"
    POSITIVE: str = "#22c55e"
    NEGATIVE: str = "#9ca3af"
    ACCENT: str = "#06b6d4"
    TEXT_PRIMARY: str = "#e5e7eb"
    TEXT_MUTED: str = "#9ca3af"


# --- Grid configuration (layout sizing & counts) ---
@dataclass(frozen=True)
class GridConfig:
    TILE_SIZE: int = 160   # px
    TILE_RADIUS: int = 24  # px
    OUTLINE_RADIUS: int = 21  # px
    OUTLINE_WIDTH: int = 4  # px
    GRID_COUNT: int = 9     # 3x3 grid


# --- Game rules ---
@dataclass(frozen=True)
class GameRules:
    MIN_CORRECT: int = 2
    MAX_CORRECT: int = 5   # keep your original limit


# --- Paths (from your existing paths module) ---
@dataclass(frozen=True)
class Paths:
    ASSETS: str = ASSETS_DIR
    IMAGES: str = IMAGES_DIR


# --- Debug/diagnostics flags ---
@dataclass(frozen=True)
class DebugConfig:
    # Fixed RNG seed for reproducible rounds (None = random each run)
    RANDOM_SEED: Optional[int] = None
    # If True, re-seed each round deterministically (for round-by-round tests)
    RANDOM_SEED_PER_ROUND: bool = False
    # If True and RANDOM_SEED is None, log the auto-seed chosen at startup
    LOG_RANDOM_SEED: bool = False
    # Route sound debug prints (ui/sounds.py)
    SOUND_VERBOSE: bool = False
    # General application verbosity (future logging integration)
    VERBOSE: bool = False


# --- Aggregated settings singleton ---
@dataclass(frozen=True)
class Settings:
    THEME: UITheme = UITheme()
    GRID: GridConfig = GridConfig()
    RULES: GameRules = GameRules()
    PATHS: Paths = Paths()
    DEBUG: DebugConfig = DebugConfig()


SETTINGS = Settings()
