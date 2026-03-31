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


def fetch_images(queries: list[str], output_dir: str = "/tmp/reels_images", custom_images: list[str] = None) -> list[str]:
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    image_paths = []

    # 1. Custom uploaded images first
    if custom_images:
        for i, url in enumerate(custom_images):
            try:
                r = requests.get(url, timeout=15)
                r.raise_for_status()
                path = f"{output_dir}/image_{i:02d}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                image_paths.append(path)
                print(f"  ✓ Image {i+1} [Custom upload]")
            except Exception as e:
                print(f"  ⚠ Custom image {i+1} failed: {e}")

    # 2. Fill remaining slots with Unsplash/Pexels
    needed = max(0, len(queries) - len(image_paths))
    offset = len(image_paths)

    for i, query in enumerate(queries[:needed]):
        idx = offset + i
        modifier = LUXURY_MODIFIERS[idx % len(LUXURY_MODIFIERS)]
        img_url = None
        source = None

        # Unsplash 특정 키워드
        img_url = _unsplash(query, modifier)
        if img_url:
            source = f"Unsplash: {_shorten(query)} {modifier}"

        # Pexels 특정 키워드
        if not img_url:
            img_url = _pexels(query)
            if img_url:
                source = f"Pexels: {_shorten(query)}"

        # Unsplash fallback
        if not img_url:
            img_url = _unsplash(FALLBACK_QUERY, modifier)
            if img_url:
                source = f"Unsplash fallback"

        # Pexels fallback
        if not img_url:
            img_url = _pexels(FALLBACK_QUERY)
            if img_url:
                source = f"Pexels fallback"

        if not img_url:
            raise RuntimeError(f"All image sources failed for query: {query}")

        img_response = requests.get(img_url, timeout=15)
        img_response.raise_for_status()

        path = f"{output_dir}/image_{idx:02d}.jpg"
        with open(path, "wb") as f:
            f.write(img_response.content)
        image_paths.append(path)
        print(f"  ✓ Image {idx+1} [{source}]")

    return image_paths


if __name__ == "__main__":
    paths = fetch_images(["silk dress atelier", "ceramic tableware", "candlelight interior"])
    print(paths)
