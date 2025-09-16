from dataclasses import dataclass

from paths import ASSETS_DIR, IMAGES_DIR


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


@dataclass(frozen=True)
class GridConfig:
    TILE_SIZE: int = 160  # px
    TILE_RADIUS: int = 24  # px
    OUTLINE_RADIUS: int = 21  # px
    OUTLINE_WIDTH: int = 4  # px
    GRID_COUNT: int = 9  # 3x3


@dataclass(frozen=True)
class GameRules:
    MIN_CORRECT: int = 2
    MAX_CORRECT: int = 5


@dataclass(frozen=True)
class Paths:
    ASSETS: str = ASSETS_DIR
    IMAGES: str = IMAGES_DIR


@dataclass(frozen=True)
class DebugConfig:
    RANDOM_SEED: int | None = None  # set to an int for reproducible random rounds


@dataclass(frozen=True)
class Settings:
    THEME: UITheme = UITheme()
    GRID: GridConfig = GridConfig()
    RULES: GameRules = GameRules()
    PATHS: Paths = Paths()
    DEBUG: DebugConfig = DebugConfig()


SETTINGS = Settings()
