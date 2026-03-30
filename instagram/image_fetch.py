import os
import requests
from pathlib import Path

UNSPLASH_ACCESS_KEY = os.environ["UNSPLASH_ACCESS_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

UNSPLASH_API = "https://api.unsplash.com/photos/random"
PEXELS_API = "https://api.pexels.com/v1/search"

LUXURY_MODIFIERS = ["editorial", "minimal", "luxury", "soft light", "moody"]
FALLBACK_QUERY = "luxury lifestyle"


def _shorten(query: str, max_words: int = 3) -> str:
    return " ".join(query.split()[:max_words])


def _unsplash(query: str, modifier: str) -> str | None:
    full_query = f"{_shorten(query)} {modifier}"
    params = {
        "query": full_query,
        "orientation": "portrait",
        "content_filter": "high",
    }
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    try:
        r = requests.get(UNSPLASH_API, params=params, headers=headers, timeout=10)
        if r.ok:
            data = r.json()
            photo = data if isinstance(data, dict) else data[0]
            return photo["urls"]["regular"]
    except Exception:
        pass
    return None


def _pexels(query: str) -> str | None:
    params = {
        "query": _shorten(query),
        "orientation": "portrait",
        "per_page": 5,
        "size": "large",
    }
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        r = requests.get(PEXELS_API, params=params, headers=headers, timeout=10)
        if r.ok:
            photos = r.json().get("photos", [])
            if photos:
                return photos[0]["src"]["large"]
    except Exception:
        pass
    return None


def fetch_images(queries: list[str], output_dir: str = "/tmp/reels_images") -> list[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    image_paths = []

    for i, query in enumerate(queries):
        modifier = LUXURY_MODIFIERS[i % len(LUXURY_MODIFIERS)]
        img_url = None
        source = None

        # 1. Unsplash 특정 키워드
        img_url = _unsplash(query, modifier)
        if img_url:
            source = f"Unsplash: {_shorten(query)} {modifier}"

        # 2. Pexels 특정 키워드
        if not img_url:
            img_url = _pexels(query)
            if img_url:
                source = f"Pexels: {_shorten(query)}"

        # 3. Unsplash fallback 키워드
        if not img_url:
            img_url = _unsplash(FALLBACK_QUERY, modifier)
            if img_url:
                source = f"Unsplash fallback: {FALLBACK_QUERY} {modifier}"

        # 4. Pexels fallback 키워드
        if not img_url:
            img_url = _pexels(FALLBACK_QUERY)
            if img_url:
                source = f"Pexels fallback: {FALLBACK_QUERY}"

        if not img_url:
            raise RuntimeError(f"All image sources failed for query: {query}")

        # Download
        img_response = requests.get(img_url, timeout=15)
        img_response.raise_for_status()

        path = f"{output_dir}/image_{i:02d}.jpg"
        with open(path, "wb") as f:
            f.write(img_response.content)
        image_paths.append(path)
        print(f"  ✓ Image {i+1} [{source}]")

    return image_paths


if __name__ == "__main__":
    paths = fetch_images(["silk dress atelier", "ceramic tableware", "candlelight interior"])
    print(paths)
