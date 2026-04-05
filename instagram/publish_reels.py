"""
Instagram Reels Auto-Publisher
Orchestrates: schedule → script → images → video → publish
"""

import sys
from post_schedule import get_post_config
from script_gen import generate_script
from image_fetch import fetch_images
from music_fetch import fetch_music
from video_gen import build_video
from instagram import publish_reel


def main():
    print("=" * 50)
    print("Instagram Reels Pipeline Starting")
    print("=" * 50)

    # 1. Determine today's post config
    print("\n[1/5] Determining schedule...")
    config = get_post_config()
    category = config["category"]
    post_format = config["format"]
    print(f"  Category : {category}")
    print(f"  Format   : {post_format}")
    print(f"  Time     : {config['timestamp']}")

    # 2. Generate script via Claude API
    print(f"\n[2/5] Generating {post_format} script ({category})...")
    script = generate_script(category, post_format)
    print(f"  ✓ Script generated")

    # 3. Fetch images from Unsplash
    print("\n[3/6] Fetching images from Unsplash...")
    custom_images = script.get("custom_images", [])
    image_paths = fetch_images(script["unsplash_queries"], custom_images=custom_images)
    print(f"  ✓ {len(image_paths)} images fetched")

    # 4. Fetch background music from Pixabay
    print(f"\n[4/6] Fetching music ({category} / {post_format})...")
    music_path = fetch_music(category, post_format)

    # 5. Build video with ffmpeg
    print("\n[5/6] Rendering video...")
    output_video = "/tmp/reel_output.mp4"
    build_video(script["scenes"], image_paths, output_video, music_path=music_path)

    # 6. Publish to Instagram
    print("\n[6/6] Publishing to Instagram...")
    media_id = publish_reel(
        video_path=output_video,
        caption=script["caption"],
        hashtags=script["hashtags"],
    )

    print("\n" + "=" * 50)
    print(f"✓ Done. Published media ID: {media_id}")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)
