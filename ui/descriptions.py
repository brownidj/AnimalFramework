import os
import json

# Cached descriptions loaded from assets/animal_descriptions.json
_DESCRIPTIONS_CACHE = None

def _load_descriptions():
    """Load and cache animal descriptions from assets/animal_descriptions.json."""
    global _DESCRIPTIONS_CACHE
    if _DESCRIPTIONS_CACHE is not None:
        return _DESCRIPTIONS_CACHE
    path = os.path.join("assets", "animal_descriptions.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _DESCRIPTIONS_CACHE = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        _DESCRIPTIONS_CACHE = {}
    return _DESCRIPTIONS_CACHE

def _description_for(image_file):
    """Return best-match description for a given image filename."""
    data = _load_descriptions()
    base = os.path.basename(image_file)
    stem, _ = os.path.splitext(base)
    candidates = [base, stem, stem.replace("_", " ")]
    for key in candidates:
        if key in data and isinstance(data[key], str):
            return data[key]
    return "No description available for this animal yet."