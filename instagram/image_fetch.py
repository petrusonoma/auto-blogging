import os
import requests
from pathlib import Path

UNSPLASH_ACCESS_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
UNSPLASH_API = "https://api.unsplash.com/photos/random"

# Mood modifiers that keep visuals in the quiet luxury register
LUXURY_MODIFIERS = ["editorial", "minimal", "luxury", "soft light", "moody"]


def fetch_images(queries: list[str], output_dir: str = "/tmp/reels_images") -> list[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    image_paths = []

    for i, query in enumerate(queries):
        # Limit query to 4 words max, then add one mood modifier
        words = query.split()[:4]
        short_query = " ".join(words)
        modifier = LUXURY_MODIFIERS[i % len(LUXURY_MODIFIERS)]
        full_query = f"{short_query} {modifier}"

        params = {
            "query": full_query,
            "orientation": "portrait",   # 9:16 friendly
            "content_filter": "high",
        }
        headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

        response = requests.get(UNSPLASH_API, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        # API returns list when count > 1, dict when count == 1 — handle both
        photo = data if isinstance(data, dict) else data[0]

        img_url = photo["urls"]["regular"]
        img_response = requests.get(img_url, timeout=15)
        img_response.raise_for_status()

        path = f"{output_dir}/image_{i:02d}.jpg"
        with open(path, "wb") as f:
            f.write(img_response.content)
        image_paths.append(path)
        print(f"  ✓ Image {i+1}: {full_query}")

    return image_paths


if __name__ == "__main__":
    paths = fetch_images(["silk dress atelier", "ceramic tableware", "candlelight interior"])
    print(paths)
