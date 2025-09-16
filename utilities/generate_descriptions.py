# scripts/generate_descriptions.py
import os
import re
import json
from typing import Dict, List
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# Config
# ---------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "assets", "images")
OUT_JSON = os.path.join(PROJECT_ROOT, "assets", "animal_descriptions.json")

MODEL = "gpt-4o-mini"  # fast + cost-effective; bump to 'gpt-4o' if you want
APPROX_WORDS = 100

# --- API key loaded from .env ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------------
# Pluralisation helpers
# ---------------------------
IRREGULAR = {
    # common animal irregulars
    "aardwolf": "aardwolves",
    "wolf": "wolves",
    "calf": "calves",
    "leaf": "leaves",
    "mouse": "mice",
    "louse": "lice",
    "goose": "geese",
    "man": "men",
    "woman": "women",
    "person": "people",
    "ox": "oxen",
    "child": "children",
    "tooth": "teeth",
    "foot": "feet",
    # invariant plurals
    "bass": "bass",
    "sheep": "sheep",
    "fish": "fish",
    "deer": "deer",
    "bison": "bison",
    "moose": "moose",
    "salmon": "salmon",
    "trout": "trout",
    "prawn": "prawn",
    "lynx": "lynx",
    # regionally accepted forms
    "octopus": "octopuses",
    "platypus": "platypuses",
    "butterfly": "butterflies",
    "bilby": "bilbies",
}

SUFFIX_RULES = (
    (re.compile(r"(?i)([^aeiou])y$"), r"\1ies"),       # butterfly -> butterflies
    (re.compile(r"(?i)(s|x|z|ch|sh)$"), r"\1es"),      # fox -> foxes, bass -> basses
)

def titleize_stem(stem: str) -> str:
    """'fur_seal' -> 'Fur seal'"""
    parts = stem.replace("-", " ").replace("_", " ").split()
    if not parts:
        return stem
    parts = [parts[0].capitalize()] + [p.lower() for p in parts[1:]]
    return " ".join(parts)

def infer_plural(common_name: str) -> str:
    """
    Returns the plural of the LAST word in common_name, preserving casing,
    and reattaches earlier words unchanged.
    e.g. 'Fur seal' -> 'Fur seals'; 'Aardwolf' -> 'Aardwolves'
    """
    words = common_name.strip().split()
    if not words:
        return common_name
    last = words[-1]
    cap = last[:1].isupper()
    base = last.lower()

    if base in IRREGULAR:
        plural_last = IRREGULAR[base]
    else:
        plural_last = base
        applied = False
        for patt, repl in SUFFIX_RULES:
            if patt.search(base):
                plural_last = patt.sub(repl, base)
                applied = True
                break
        if not applied:
            if base.endswith("f"):
                plural_last = base[:-1] + "ves"
            elif base.endswith("fe"):
                plural_last = base[:-2] + "ves"
            else:
                plural_last = base + "s"
    if cap:
        plural_last = plural_last[0].upper() + plural_last[1:]
    words[-1] = plural_last
    return " ".join(words)

# ---------------------------
# I/O helpers
# ---------------------------
def list_png_stems(images_dir: str) -> List[str]:
    if not os.path.isdir(images_dir):
        return []
    stems = []
    for fn in os.listdir(images_dir):
        if fn.lower().endswith(".png"):
            stems.append(os.path.splitext(fn)[0])  # no extension
    stems.sort(key=str.lower)
    return stems

def load_json(path: str) -> Dict[str, str]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                raise SystemExit("ERROR: existing animal_descriptions.json is not valid JSON.")
    return {}

def save_json(path: str, data: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------
# OpenAI call
# ---------------------------
def build_prompt(common_name: str) -> str:
    plural_phrase = infer_plural(common_name) + " are"
    return (
        "Write ONE paragraph in UK English of about " + str(APPROX_WORDS) + " words about the animal '"
        + common_name + "'. Begin the paragraph EXACTLY with: '" + plural_phrase +
        "'. Cover habitat, diet, notable traits/behaviour, and conservation context if relevant. "
        "Use a clear, engaging natural-history tone. No lists, no headings, no quotes. Output only the paragraph."
    )

def generate_description(common_name: str) -> str:
    prompt = build_prompt(common_name)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a concise zoology writer who always uses UK English spelling."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=220,
    )
    return resp.choices[0].message.content.strip()

# ---------------------------
# Sorting helper
# ---------------------------
def sort_json_by_key():
    if not os.path.exists(OUT_JSON):
        return
    data = load_json(OUT_JSON)
    sorted_data = dict(sorted(data.items()))
    save_json(OUT_JSON, sorted_data)
    print("Sorted " + OUT_JSON)

# ---------------------------
# Main
# ---------------------------
def generate():
    stems = list_png_stems(IMAGES_DIR)
    if not stems:
        print("No PNGs found in:", IMAGES_DIR)
        return

    data = load_json(OUT_JSON)
    added = 0

    for stem in stems:
        if stem in data and isinstance(data[stem], str) and data[stem].strip():
            continue  # keep existing
        common_name = titleize_stem(stem)
        try:
            desc = generate_description(common_name)
            # sanity: enforce required start
            required_start = infer_plural(common_name) + " are"
            if not desc.lower().startswith(required_start.lower()):
                desc = required_start + " " + desc.lstrip()
            data[stem] = desc
            added += 1
            print("Added description for " + stem)
        except Exception as e:
            print(f"ERROR generating {stem}: {e}")

    if added:
        save_json(OUT_JSON, data)
        sort_json_by_key()
        print("Saved " + str(added) + " new description(s) to " + OUT_JSON)
    else:
        print("All images already had descriptions.")

if __name__ == "__main__":
    # generate()
    sort_json_by_key()