import os
import requests
import random
from pathlib import Path

PIXABAY_API_KEY = os.environ["PIXABAY_API_KEY"]
PIXABAY_API = "https://pixabay.com/api/videos/music/"

# Genre mapping by category and format
GENRE_MAP = {
    "fashion": {
        "story": ["ambient", "cinematic"],
        "top3": ["minimal", "ambient"],
    },
    "living": {
        "story": ["ambient", "classical"],
        "top3": ["ambient", "classical"],
    },
}


def fetch_music(category: str, post_format: str, output_dir: str = "/tmp/reels_music") -> str:
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    genres = GENRE_MAP.get(category, {}).get(post_format, ["ambient"])
    genre = random.choice(genres)

    params = {
        "key": PIXABAY_API_KEY,
        "genre": genre,
        "per_page": 20,
    }

    response = requests.get(PIXABAY_API, params=params, timeout=10)
    response.raise_for_status()

    hits = response.json().get("hits", [])
    if not hits:
        raise RuntimeError(f"No music found for genre: {genre}")

    # Pick a random track from results
    track = random.choice(hits)
    audio_url = track["audio"]
    track_title = track.get("title", "track")
    print(f"  ✓ Music: '{track_title}' ({genre})")

    # Download
    audio_resp = requests.get(audio_url, timeout=30)
    audio_resp.raise_for_status()

    path = f"{output_dir}/music.mp3"
    with open(path, "wb") as f:
        f.write(audio_resp.content)

    return path


if __name__ == "__main__":
    path = fetch_music("fashion", "story")
    print(path)
