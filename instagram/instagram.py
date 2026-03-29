import os
import time
import requests
import cloudinary
import cloudinary.uploader

INSTAGRAM_USER_ID = os.environ["INSTAGRAM_USER_ID"]
INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
GRAPH_API = "https://graph.instagram.com/v21.0"

cloudinary.config(
    cloudinary_url=os.environ["CLOUDINARY_URL"]
)


def upload_to_cloudinary(video_path: str) -> str:
    """Upload video to Cloudinary and return public URL."""
    print("  Uploading to Cloudinary...")
    result = cloudinary.uploader.upload(
        video_path,
        resource_type="video",
        folder="instagram_reels",
        overwrite=True,
        # Auto-generate public_id from timestamp to avoid collisions
        use_filename=False,
    )
    url = result["secure_url"]
    print(f"  ✓ Cloudinary URL: {url}")
    return url


def publish_reel(video_path: str, caption: str, hashtags: list[str]) -> str:
    """
    Full two-step Instagram Graph API Reels publish flow.
    Returns the published media ID.
    """
    # Build final caption
    tag_string = " ".join(f"#{t}" for t in hashtags)
    full_caption = f"{caption}\n\n{tag_string}"

    # Step 1: Upload video to Cloudinary for public URL
    video_url = upload_to_cloudinary(video_path)

    # Step 2: Create media container
    print("  Creating Instagram media container...")
    container_resp = requests.post(
        f"{GRAPH_API}/{INSTAGRAM_USER_ID}/media",
        data={
            "media_type": "REELS",
            "video_url": video_url,
            "caption": full_caption,
            "share_to_feed": "true",
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    container_resp.raise_for_status()
    container_id = container_resp.json()["id"]
    print(f"  ✓ Container ID: {container_id}")

    # Step 3: Poll until container is ready (video processing takes time)
    print("  Waiting for video processing...")
    for attempt in range(20):
        time.sleep(10)
        status_resp = requests.get(
            f"{GRAPH_API}/{container_id}",
            params={
                "fields": "status_code",
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            },
            timeout=15,
        )
        status_resp.raise_for_status()
        status = status_resp.json().get("status_code")
        print(f"    attempt {attempt+1}: {status}")

        if status == "FINISHED":
            break
        if status == "ERROR":
            raise RuntimeError("Instagram video processing failed")
    else:
        raise TimeoutError("Video processing timed out after 200s")

    # Step 4: Publish
    print("  Publishing Reel...")
    publish_resp = requests.post(
        f"{GRAPH_API}/{INSTAGRAM_USER_ID}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        },
        timeout=30,
    )
    publish_resp.raise_for_status()
    media_id = publish_resp.json()["id"]
    print(f"  ✓ Published! Media ID: {media_id}")

    return media_id


if __name__ == "__main__":
    print("instagram.py ready — run via publish_reels.py")
