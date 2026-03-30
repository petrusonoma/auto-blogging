import random
from pathlib import Path

# Base directory of the instagram/ folder
BASE_DIR = Path(__file__).parent
MUSIC_DIR = BASE_DIR / "music"

# Music file naming convention:
# fashion_*.mp3  → fashion posts
# living_*.mp3   → living posts
# ambient_*.mp3  → fallback for any category

CATEGORY_PREFIX = {
    "fashion": ["elegant", "cinematic", "ambient"],
    "living": ["ambient", "cinematic", "elegant"],
}


def fetch_music(category: str, post_format: str, output_dir: str = "/tmp/reels_music") -> str | None:
    """
    Select a random music file from the local music/ folder based on category.
    Returns the path to the selected file, or None if no music files found.
    """
    if not MUSIC_DIR.exists():
        print("  ⚠ music/ folder not found — skipping music")
        return None

    prefixes = CATEGORY_PREFIX.get(category, ["ambient"])
    candidates = []

    for prefix in prefixes:
        candidates.extend(MUSIC_DIR.glob(f"{prefix}_*.mp3"))
        candidates.extend(MUSIC_DIR.glob(f"{prefix}_*.m4a"))

    # Fallback: any mp3 in music/
    if not candidates:
        candidates = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.m4a"))

    if not candidates:
        print("  ⚠ No music files in music/ folder — skipping music")
        return None

    selected = random.choice(candidates)
    print(f"  ✓ Music: {selected.name}")
    return str(selected)


if __name__ == "__main__":
    path = fetch_music("fashion", "story")
    print(path)
