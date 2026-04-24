"""
post.py — Luxury Lifestyle Blog Auto-Posting Script
Runs via GitHub Actions twice daily.

Required GitHub Secrets:
  - ANTHROPIC_API_KEY
  - GOOGLE_CLIENT_ID
  - GOOGLE_CLIENT_SECRET
  - GOOGLE_REFRESH_TOKEN
  - BLOG_ID
  - UNSPLASH_ACCESS_KEY
  - PEXELS_API_KEY
  - INSTAGRAM_ACCESS_TOKEN
  - INSTAGRAM_USER_ID
  - CLOUDINARY_URL
"""

import os
import random
import requests
import cloudinary
import cloudinary.uploader
from datetime import datetime

# ──────────────────────────────────────────
# Load environment variables
# ──────────────────────────────────────────
ANTHROPIC_API_KEY      = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CLIENT_ID       = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET   = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REFRESH_TOKEN   = os.environ["GOOGLE_REFRESH_TOKEN"]
BLOG_ID                = os.environ["BLOG_ID"]
UNSPLASH_ACCESS_KEY    = os.environ["UNSPLASH_ACCESS_KEY"]
PEXELS_API_KEY         = os.environ["PEXELS_API_KEY"]
INSTAGRAM_ACCESS_TOKEN = os.environ["INSTAGRAM_ACCESS_TOKEN"]
INSTAGRAM_USER_ID      = os.environ["INSTAGRAM_USER_ID"]
CLOUDINARY_URL         = os.environ["CLOUDINARY_URL"]
PINTEREST_ACCESS_TOKEN = os.environ["PINTEREST_ACCESS_TOKEN"]

cloudinary.config(cloudinary_url=CLOUDINARY_URL)

# Pinterest board mapping per topic
PINTEREST_BOARDS = {
    "Cars":    "1118511326145096379",  # Dream Cars & Drives
    "Travel":  "1118511326145096380",  # Luxury Travel & Hotels
    "Sports":  "1118511326145096381",  # Sports
    "Fashion": "1118511326145096383",  # Fashion & Style
    "Living":  "1118511326145096385",  # Interior Design & Living
}

# ──────────────────────────────────────────
# Get Google Access Token
# ──────────────────────────────────────────
def get_access_token():
    res = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id":     GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": GOOGLE_REFRESH_TOKEN,
        "grant_type":    "refresh_token",
    })
    res.raise_for_status()
    token = res.json().get("access_token")
    if not token:
        raise Exception("Failed to get access token")
    print("✅ Google access token obtained")
    return token

# ──────────────────────────────────────────
# Get recent post titles from Blogger
# ──────────────────────────────────────────
def get_recent_titles(access_token: str, max_results: int = 10) -> list:
    try:
        url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts"
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get(url, headers=headers, params={"maxResults": max_results, "fields": "items/title"})
        res.raise_for_status()
        items = res.json().get("items", [])
        titles = [item["title"] for item in items if "title" in item]
        print(f"📋 Recent titles fetched: {len(titles)} posts")
        return titles
    except Exception as e:
        print(f"⚠️ Could not fetch recent titles: {e}")
        return []

# ──────────────────────────────────────────
# Topic fallback keywords
# ──────────────────────────────────────────
TOPIC_FALLBACKS = {
    "Cars":    "luxury car",
    "Travel":  "luxury hotel",
    "Sports":  "sports stadium",
    "Fashion": "fashion runway",
    "Living":  "luxury interior",
}

# ──────────────────────────────────────────
# Unsplash
# ──────────────────────────────────────────
def fetch_unsplash_image(keyword: str) -> dict:
    try:
        res = requests.get(
            "https://api.unsplash.com/search/photos",
            params={"query": keyword, "per_page": 5, "orientation": "landscape", "content_filter": "high"},
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
        )
        res.raise_for_status()
        results = res.json().get("results", [])
        if results:
            print(f"✅ Unsplash image found: {keyword}")
            photo = random.choice(results)
            return {
                "url": photo["urls"]["regular"],
                "alt": photo.get("alt_description") or keyword,
                "photographer": photo["user"]["name"],
                "photographer_url": photo["user"]["links"]["html"],
                "source": "Unsplash",
                "source_url": "https://unsplash.com",
            }
        print(f"⚠️ No Unsplash image for: {keyword}")
    except Exception as e:
        print(f"⚠️ Unsplash failed for '{keyword}': {e}")
    return None

# ──────────────────────────────────────────
# Pexels
# ──────────────────────────────────────────
def fetch_pexels_image(keyword: str) -> dict:
    try:
        res = requests.get(
            "https://api.pexels.com/v1/search",
            params={"query": keyword, "per_page": 5, "orientation": "landscape"},
            headers={"Authorization": PEXELS_API_KEY},
        )
        res.raise_for_status()
        photos = res.json().get("photos", [])
        if photos:
            print(f"✅ Pexels image found: {keyword}")
            photo = random.choice(photos)
            return {
                "url": photo["src"]["large"],
                "alt": photo.get("alt") or keyword,
                "photographer": photo["photographer"],
                "photographer_url": photo["photographer_url"],
                "source": "Pexels",
                "source_url": "https://www.pexels.com",
            }
        print(f"⚠️ No Pexels image for: {keyword}")
    except Exception as e:
        print(f"⚠️ Pexels failed for '{keyword}': {e}")
    return None

# ──────────────────────────────────────────
# Image fetch: Unsplash → Pexels → fallback
# ──────────────────────────────────────────
def fetch_image(keyword: str, topic: str = "") -> dict:
    fallback = TOPIC_FALLBACKS.get(topic, "")

    image = fetch_unsplash_image(keyword)
    if image:
        return image

    print("⚠️ Unsplash failed, trying Pexels...")
    image = fetch_pexels_image(keyword)
    if image:
        return image

    if fallback:
        print("⚠️ Pexels failed, trying Unsplash fallback...")
        image = fetch_unsplash_image(fallback)
        if image:
            return image

    if fallback:
        print("⚠️ Trying Pexels fallback...")
        image = fetch_pexels_image(fallback)
        if image:
            return image

    return None

# ──────────────────────────────────────────
# Upload to Cloudinary
# ──────────────────────────────────────────
def upload_to_cloudinary(image_url: str) -> str:
    try:
        result = cloudinary.uploader.upload(
            image_url,
            folder="luxury_blog",
            resource_type="image",
            transformation=[
                {"width": 1080, "height": 1080, "crop": "fill", "gravity": "center"},
                {"quality": "auto", "fetch_format": "jpg"},
            ]
        )
        public_url = result.get("secure_url")
        print(f"✅ Uploaded to Cloudinary: {public_url[:60]}...")
        return public_url
    except Exception as e:
        print(f"⚠️ Cloudinary upload failed: {e}")
        return None

# ──────────────────────────────────────────
# Post to Instagram
# ──────────────────────────────────────────
def post_to_instagram(image_url: str, caption: str, hashtags: str) -> bool:
    try:
        full_caption = f"{caption}\n\n🔗 Full article — link in bio\n\n{hashtags}"

        cloudinary_url = upload_to_cloudinary(image_url)
        if not cloudinary_url:
            print("⚠️ Skipping Instagram — Cloudinary upload failed")
            return False

        container_res = requests.post(
            f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media",
            data={
                "image_url": cloudinary_url,
                "caption": full_caption,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            }
        )
        container_res.raise_for_status()
        container_id = container_res.json().get("id")
        if not container_id:
            print("⚠️ Failed to create Instagram media container")
            return False
        print(f"✅ Instagram container created: {container_id}")

        import time
        for attempt in range(10):
            time.sleep(5)
            status_res = requests.get(
                f"https://graph.instagram.com/v21.0/{container_id}",
                params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN}
            )
            status = status_res.json().get("status_code", "")
            print(f"    attempt {attempt+1}: {status}")
            if status == "FINISHED":
                break

        publish_res = requests.post(
            f"https://graph.instagram.com/v21.0/{INSTAGRAM_USER_ID}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": INSTAGRAM_ACCESS_TOKEN,
            }
        )
        publish_res.raise_for_status()
        post_id = publish_res.json().get("id")
        print(f"✅ Instagram post published: {post_id}")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"⚠️ Instagram posting failed: {e}")
        print(f"⚠️ Response body: {e.response.text}")
        return False
    except Exception as e:
        print(f"⚠️ Instagram posting failed: {e}")
        return False

# ──────────────────────────────────────────
# Common style guide
# ──────────────────────────────────────────
COMMON_STYLE = """
[Writing Style Guide]
- Language: English only
- Voice: Sophisticated luxury lifestyle magazine editor — think Robb Report, Vogue, Monocle
- Audience: Globally-minded readers with a taste for high-end culture, travel, and design
- Tone: Authoritative yet evocative. Informed without being academic. Never breathless or hyperbolic.
- Forbidden: "the best ever", "you won't believe", "game changer", "must-have", clickbait phrasing
- Length: 700-900 words of body copy
- Format: Strictly follow this HTML structure:
    <h2>Section heading</h2>
    <p>Body paragraph...</p>
    <h3>Sub-section heading (if needed)</h3>
    <p>Body paragraph...</p>
- Fifth to last line: [INSTAGRAM]2-3 sentence Instagram caption summarizing the article's essence, evocative and elegant tone, no hashtags[/INSTAGRAM]
- Fourth to last line: [HASHTAGS]10-15 relevant Instagram hashtags for this specific article, mix of broad and niche tags, always include #luxury and #whereveryonedreams, no spaces within each tag, space-separated with # symbol (e.g. #rollsroyce #luxurycars #britishluxury #grandtouring #luxury #whereveryonedreams)[/HASHTAGS]
- Third to last line: [LABELS]3-5 specific keyword labels relevant to this exact article, comma-separated[/LABELS]
- Second to last line: [IMAGE]2-4 word search keyword for a beautiful hero image[/IMAGE]
- Final line: [META]Up to 155 characters of SEO meta description in English[/META]
- Reference today's date for recency: {date}
- IMPORTANT: The following topics have already been covered recently. Do NOT repeat them — choose a clearly different subject, brand, destination, or angle:
{recent_titles}
""".format(
    date=datetime.now().strftime("%B %Y"),
    recent_titles="{recent_titles}"
)

SYSTEM_PROMPT = """You are a senior editor at a world-class luxury lifestyle magazine,
writing at the level of Robb Report, Conde Nast Traveller, and Monocle.
Your prose is refined, precise, and quietly confident.
You deliver inspiration and beauty alongside information — never mere facts alone.
All content must be written in fluent, editorial-quality English."""

# ──────────────────────────────────────────
# Per-topic prompts
# ──────────────────────────────────────────
PROMPTS = {
    "Cars": """
[Topic] Luxury Automotive
[Brands] Mercedes-Benz, Audi, BMW, Land Rover, Porsche, Bentley, Rolls-Royce, Ferrari, Lamborghini, Aston Martin
[Angle - choose one at random]
1. New model or facelift reveal - design philosophy, engineering innovation, interior craftsmanship
2. In-depth model essay - the driving experience, material quality, sensory impression
3. Luxury EV transition - how heritage brands are reimagining performance for the electric era
4. Limited edition or special series - rarity, collector value, the story behind the build
[Writing guidance]
- Lead with the experience, not the spec sheet
- Describe design language, material choices, and artisanal details with specificity
- Price context is welcome; frame it as value, not a number
[Title examples]
- "The New Rolls-Royce Spectre: Where Silence Becomes the Statement"
- "Porsche Taycan Cross Turismo: Redefining What a Driver's Car Can Be"
""",

    "Travel": """
[Topic] Luxury International Travel & Hotels (no domestic South Korea content)
[Hotel brands] Four Seasons, Aman, Rosewood, Mandarin Oriental, The Ritz-Carlton,
               Bulgari Hotels, Six Senses, Banyan Tree, Park Hyatt, Belmond
[Angle - choose one at random]
1. City luxury travel guide - hotel, dining, and experience curation for a specific destination
2. Iconic hotel portrait - history, architecture, signature service philosophy
3. Rare stays - private islands, overwater villas, remote retreats
4. Culinary travel - Michelin-starred dining and fine-dining culture in a specific city or region
[Writing guidance]
- Paint the destination: light, air, texture, atmosphere
- Focus on what you will feel and experience, not just where you should go
- Suite categories, views, spa, and F&B details should feel like a private recommendation
[Title examples]
- "Aman Venice: Living Inside a Palazzo, Quietly and Completely"
- "The Amalfi Coast in Seven Days: A Study in Dolce Far Niente"
""",

    "Sports": """
[Topic] Luxury Sports
[This post must focus on one of the following - rotate and avoid repeating the same sport consecutively]:
- Formula 1 (Monaco, Silverstone, Monza, driver stories, team culture)
- Tennis (Wimbledon, Roland-Garros, US Open, player profiles)
- Football (EPL or La Liga - club stories, iconic players, stadium culture)
Pick whichever sport has NOT appeared in the recent titles list above.
[Important] No match result recaps or scorecard summaries.
[Angle - choose one at random]
1. A season-defining moment - the strategy, the drama, what it means for the sport
2. A legend's milestone or farewell - career arc, legacy, cultural weight
3. Where sport meets luxury - F1 team sponsorships, watchmaking partnerships, tennis fashion
4. The host city as a destination - culture, lifestyle, and glamour surrounding a Grand Prix or Grand Slam
5. A rising star - a deep profile of the next generation's defining talent
[Writing guidance]
- Sport journalism meets luxury magazine sensibility
- Narrative and emotion over numbers and statistics
[Title examples]
- "Monaco Grand Prix: The Race That Exists to Be Watched"
- "Carlos Alcaraz: The Clay-Court King Writing a New Chapter"
""",

    "Fashion": """
[Topic] Luxury Fashion
[Brands] Chanel, Louis Vuitton, Hermes, Dior, Gucci, Prada, Valentino, Bottega Veneta,
         Saint Laurent, Celine, Loewe, Balenciaga, Loro Piana, Brunello Cucinelli
[Angle - choose one at random]
1. Fashion week highlight - a single collection reviewed in depth (Paris, Milan, New York, or London)
2. Celebrity fashion analysis - red carpet or off-duty looks read as cultural statements
3. Iconic piece - the history and enduring value of a brand's signature item
4. Designer profile - a creative director's vision, references, and aesthetic philosophy
5. Season trend report - the key codes of luxury fashion this season, with specific looks
[Writing guidance]
- Treat fashion as culture, art, and philosophy - not just clothing
- Describe silhouette, fabric, colour palette, and construction with editorial precision
[Title examples]
- "Dior Haute Couture: Maria Grazia Chiuri's Portrait of Femininity, Revisited"
- "Zendaya's Red-Carpet Philosophy: Fashion as Storytelling"
""",

    "Living": """
[Topic] Luxury Living - Furniture, Tableware, Lighting, Objects
[Brands & categories]
- Furniture: Minotti, B&B Italia, Poltrona Frau, Cassina, Molteni&C, Knoll, De Sede
- Tableware: Hermes Maison, Christofle, Bernardaud, Ginori 1735, Meissen, Puiforcat
- Lighting: Flos, Louis Poulsen, Artemide, Apparatus Studio, Roll & Hill
- Objects & decor: Murano glassware, Trudon candles, art objects, bespoke ceramics
[Angle - choose one at random]
1. Brand portrait - heritage, artisanal process, signature collection
2. Space curation - how to compose a specific room at the luxury level
3. New collection or collaboration - a notable new release and the designer behind it
4. The art of the table - fine dining at home, from linen to crystal to silverware
[Writing guidance]
- Let the reader feel the weight of polished silver, the warmth of cashmere, the cool of marble
- Centre the sensory experience the object creates, not its product specifications
[Title examples]
- "Minotti's 2025 Collection: The Italian Art of Living, Refined Once More"
- "Setting the Table: A Guide to the Fine Art of Home Dining with Christofle"
""",
}

# Weekly topic schedule (Monday = 0)
# Format: {weekday: (morning_topic, evening_topic)}
# KST 08:00 = UTC 23:00 (prev day), KST 19:00 = UTC 10:00
WEEKLY = {
    0: ("Travel",  "Cars"),      # Monday
    1: ("Living",  "Fashion"),   # Tuesday
    2: ("Sports",  "Travel"),    # Wednesday
    3: ("Cars",    "Living"),    # Thursday
    4: ("Fashion", "Sports"),   # Friday
    5: ("Travel",  "Cars"),      # Saturday
    6: ("Living",  "Travel"),   # Sunday
}

# ──────────────────────────────────────────
# Step 1: Generate post with Claude
# ──────────────────────────────────────────
def generate_post(topic: str, recent_titles: list) -> dict:
    if recent_titles:
        recent_str = "\n".join(f"- {t}" for t in recent_titles)
    else:
        recent_str = "(none yet)"

    style = COMMON_STYLE.replace("{recent_titles}", recent_str)
    prompt = style + PROMPTS[topic]

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-4-6",
            "max_tokens": 2048,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    raw = response.json()["content"][0]["text"]

    # Extract META
    meta = ""
    if "[META]" in raw and "[/META]" in raw:
        meta = raw.split("[META]")[1].split("[/META]")[0].strip()
        raw = raw.split("[META]")[0].strip()

    # Extract IMAGE keyword
    image_keyword = TOPIC_FALLBACKS.get(topic, topic.lower())
    if "[IMAGE]" in raw and "[/IMAGE]" in raw:
        image_keyword = raw.split("[IMAGE]")[1].split("[/IMAGE]")[0].strip()
        raw = raw.split("[IMAGE]")[0].strip()

    # Extract LABELS
    labels = []
    if "[LABELS]" in raw and "[/LABELS]" in raw:
        labels_str = raw.split("[LABELS]")[1].split("[/LABELS]")[0].strip()
        labels = [l.strip() for l in labels_str.split(",") if l.strip()]
        raw = raw.split("[LABELS]")[0].strip()

    # Extract HASHTAGS
    hashtags = "#luxury #luxurylifestyle #whereveryonedreams"
    if "[HASHTAGS]" in raw and "[/HASHTAGS]" in raw:
        hashtags = raw.split("[HASHTAGS]")[1].split("[/HASHTAGS]")[0].strip()
        raw = raw.split("[HASHTAGS]")[0].strip()

    # Extract INSTAGRAM caption
    instagram_caption = ""
    if "[INSTAGRAM]" in raw and "[/INSTAGRAM]" in raw:
        instagram_caption = raw.split("[INSTAGRAM]")[1].split("[/INSTAGRAM]")[0].strip()
        raw = raw.split("[INSTAGRAM]")[0].strip()

    # Always include topic as first label
    if topic not in labels:
        labels = [topic] + labels

    # Separate title from body
    lines = raw.strip().split("\n")
    title = lines[0].replace("#", "").strip()
    content = "\n".join(lines[1:]).strip()

    if content.startswith("<h2>") or len(title) > 100:
        title = f"Luxury {topic} — {datetime.now().strftime('%B %d, %Y')}"
        content = raw

    print(f"✅ Post generated: {title}")
    print(f"🏷️ Labels: {labels}")
    print(f"🔍 Image keyword: {image_keyword}")
    print(f"📱 Instagram caption: {instagram_caption[:60]}...")
    print(f"# Hashtags: {hashtags[:60]}...")
    return {
        "title": title,
        "content": content,
        "meta": meta,
        "image_keyword": image_keyword,
        "labels": labels,
        "instagram_caption": instagram_caption,
        "hashtags": hashtags,
    }

# ──────────────────────────────────────────
# Step 2: Build content with hero image
# ──────────────────────────────────────────
def build_content_with_image(content: str, image_keyword: str, topic: str) -> tuple:
    image = fetch_image(image_keyword, topic)

    if not image:
        print("⚠️ No image found from any source, posting without image")
        return content, None

    hero_html = f"""<div style="margin-bottom:32px;">
  <img src="{image['url']}" alt="{image['alt']}"
       style="width:100%;max-height:520px;object-fit:cover;display:block;" />
  <p style="font-size:11px;color:#888;margin-top:6px;text-align:right;">
    Photo by <a href="{image['photographer_url']}" target="_blank" style="color:#888;">{image['photographer']}</a>
    on <a href="{image['source_url']}" target="_blank" style="color:#888;">{image['source']}</a>
  </p>
</div>
"""
    print(f"✅ Image added from {image['source']}: {image['url'][:60]}...")
    return hero_html + content, image

# ──────────────────────────────────────────
# Step 3: Publish to Blogger
# ──────────────────────────────────────────
def post_to_blogger(title: str, content: str, labels: list, access_token: str) -> str:
    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "title": title,
        "content": content,
        "labels": labels,
    }

    res = requests.post(url, headers=headers, json=body)
    res.raise_for_status()
    result = res.json()
    blog_post_url = result.get("url", "")
    print(f"✅ Published to Blogger: {blog_post_url}")
    return blog_post_url

# ──────────────────────────────────────────
# Post to Pinterest
# ──────────────────────────────────────────
def post_to_pinterest(image_url: str, title: str, description: str, blog_url: str, topic: str) -> bool:
    """Create a Pin on the appropriate Pinterest board."""
    try:
        board_id = PINTEREST_BOARDS.get(topic)
        if not board_id:
            print(f"⚠️ No Pinterest board for topic: {topic}")
            return False

        # Upload to Cloudinary for stable URL
        cloudinary_url = upload_to_cloudinary(image_url)
        if not cloudinary_url:
            print("⚠️ Skipping Pinterest — Cloudinary upload failed")
            return False

        res = requests.post(
            "https://api.pinterest.com/v5/pins",
            headers={
                "Authorization": f"Bearer {PINTEREST_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "board_id": board_id,
                "title": title[:100],
                "description": description[:500],
                "link": blog_url,
                "media_source": {
                    "source_type": "image_url",
                    "url": cloudinary_url,
                },
            }
        )
        res.raise_for_status()
        pin_id = res.json().get("id")
        print(f"✅ Pinterest pin created: {pin_id}")
        return True

    except requests.exceptions.HTTPError as e:
        print(f"⚠️ Pinterest posting failed: {e}")
        print(f"⚠️ Response body: {e.response.text}")
        return False
    except Exception as e:
        print(f"⚠️ Pinterest posting failed: {e}")
        return False

# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────
def main():
    weekday = datetime.now().weekday()
    hour_utc = datetime.utcnow().hour
    morning_topic, evening_topic = WEEKLY.get(weekday, ("Travel", "Cars"))
    # UTC 23:00 = KST 08:00 (morning), UTC 10:00 = KST 19:00 (evening)
    topic = morning_topic if hour_utc >= 20 else evening_topic
    print(f"📌 Today's topic: {topic} (weekday: {weekday}, UTC hour: {hour_utc})")

    access_token = get_access_token()
    recent_titles = get_recent_titles(access_token, max_results=10)
    post = generate_post(topic, recent_titles)
    content_with_image, image = build_content_with_image(
        post["content"], post["image_keyword"], topic
    )
    blog_url = post_to_blogger(
        post["title"], content_with_image, post["labels"], access_token
    )

    if image:
        post_to_instagram(
            image_url=image["url"],
            caption=post["instagram_caption"],
            hashtags=post["hashtags"],
        )
        post_to_pinterest(
            image_url=image["url"],
            title=post["title"],
            description=post["instagram_caption"],
            blog_url=blog_url,
            topic=topic,
        )
    else:
        print("⚠️ Skipping Instagram and Pinterest — no image available")

if __name__ == "__main__":
    main()
