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
"""

import os
import json
import random
import requests
from datetime import datetime

# ──────────────────────────────────────────
# Load environment variables
# ──────────────────────────────────────────
ANTHROPIC_API_KEY    = os.environ["ANTHROPIC_API_KEY"]
GOOGLE_CLIENT_ID     = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
GOOGLE_REFRESH_TOKEN = os.environ["GOOGLE_REFRESH_TOKEN"]
BLOG_ID              = os.environ["BLOG_ID"]
UNSPLASH_ACCESS_KEY  = os.environ["UNSPLASH_ACCESS_KEY"]

# ──────────────────────────────────────────
# Get Google Access Token (via Refresh Token)
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
# Fetch image from Unsplash
# ──────────────────────────────────────────
def fetch_unsplash_image(keyword: str) -> dict:
    """Search Unsplash and return the best matching image."""
    try:
        res = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": keyword,
                "per_page": 5,
                "orientation": "landscape",
                "content_filter": "high",
            },
            headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
        )
        res.raise_for_status()
        results = res.json().get("results", [])
        if not results:
            return None

        photo = results[0]
        return {
            "url": photo["urls"]["regular"],
            "thumb": photo["urls"]["small"],
            "alt": photo.get("alt_description") or keyword,
            "photographer": photo["user"]["name"],
            "photographer_url": photo["user"]["links"]["html"],
            "unsplash_url": photo["links"]["html"],
        }
    except Exception as e:
        print(f"⚠️ Unsplash fetch failed: {e}")
        return None

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
- Length: 700–900 words of body copy
- Format: Strictly follow this HTML structure:
    <h2>Section heading</h2>
    <p>Body paragraph...</p>
    <h3>Sub-section heading (if needed)</h3>
    <p>Body paragraph...</p>
- Second to last line: [IMAGE]2-4 word Unsplash search keyword for a beautiful hero image (e.g. "luxury sports car", "venice canal hotel", "formula one race")[/IMAGE]
- Final line: [META]Up to 155 characters of SEO meta description in English[/META]
- Reference today's date for recency: {date}
""".format(date=datetime.now().strftime("%B %Y"))

SYSTEM_PROMPT = """You are a senior editor at a world-class luxury lifestyle magazine,
writing at the level of Robb Report, Condé Nast Traveller, and Monocle.
Your prose is refined, precise, and quietly confident.
You deliver inspiration and beauty alongside information — never mere facts alone.
All content must be written in fluent, editorial-quality English."""

# ──────────────────────────────────────────
# Per-topic prompts
# ──────────────────────────────────────────
PROMPTS = {
    "Cars": COMMON_STYLE + """
[Topic] Luxury Automotive
[Brands] Mercedes-Benz, Audi, BMW, Land Rover, Porsche, Bentley, Rolls-Royce, Ferrari, Lamborghini, Aston Martin
[Angle — choose one at random]
1. New model or facelift reveal — design philosophy, engineering innovation, interior craftsmanship
2. In-depth model essay — the driving experience, material quality, sensory impression
3. Luxury EV transition — how heritage brands are reimagining performance for the electric era
4. Limited edition or special series — rarity, collector value, the story behind the build
[Writing guidance]
- Lead with the experience, not the spec sheet
- Describe design language, material choices, and artisanal details with specificity
- Price context is welcome; frame it as value, not a number
[Title examples]
- "The New Rolls-Royce Spectre: Where Silence Becomes the Statement"
- "Porsche Taycan Cross Turismo: Redefining What a Driver's Car Can Be"
""",

    "Travel": COMMON_STYLE + """
[Topic] Luxury International Travel & Hotels (no domestic South Korea content)
[Hotel brands] Four Seasons, Aman, Rosewood, Mandarin Oriental, The Ritz-Carlton,
               Bulgari Hotels, Six Senses, Banyan Tree, Park Hyatt, Belmond
[Angle — choose one at random]
1. City luxury travel guide — hotel, dining, and experience curation for a specific destination
2. Iconic hotel portrait — history, architecture, signature service philosophy
3. Rare stays — private islands, overwater villas, remote retreats
4. Culinary travel — Michelin-starred dining and fine-dining culture in a specific city or region
[Writing guidance]
- Paint the destination: light, air, texture, atmosphere
- Focus on what you will feel and experience, not just where you should go
- Suite categories, views, spa, and F&B details should feel like a private recommendation
[Title examples]
- "Aman Venice: Living Inside a Palazzo, Quietly and Completely"
- "The Amalfi Coast in Seven Days: A Study in Dolce Far Niente"
""",

    "Sports": COMMON_STYLE + """
[Topic] Luxury Sports — Formula 1, Tennis, EPL & La Liga
[Important] No match result recaps or scorecard summaries.
[Angle — choose one at random]
1. A season-defining moment — the strategy, the drama, what it means for the sport
2. A legend's milestone or farewell — career arc, legacy, cultural weight
3. Where sport meets luxury — F1 team sponsorships, watchmaking partnerships, tennis fashion
4. The host city as a destination — culture, lifestyle, and glamour surrounding a Grand Prix or Grand Slam
5. A rising star — a deep profile of the next generation's defining talent
[Writing guidance]
- Sport journalism meets luxury magazine sensibility
- Narrative and emotion over numbers and statistics
- F1: lean into Monaco, Silverstone, Monza — the circuits that carry myth
- Tennis: Wimbledon, Roland-Garros, the US Open — tradition and theatre
[Title examples]
- "Monaco Grand Prix: The Race That Exists to Be Watched"
- "Carlos Alcaraz: The Clay-Court King Writing a New Chapter"
""",

    "Fashion": COMMON_STYLE + """
[Topic] Luxury Fashion
[Brands] Chanel, Louis Vuitton, Hermès, Dior, Gucci, Prada, Valentino, Bottega Veneta,
         Saint Laurent, Celine, Loewe, Balenciaga, Loro Piana, Brunello Cucinelli
[Angle — choose one at random]
1. Fashion week highlight — a single collection reviewed in depth (Paris, Milan, New York, or London)
2. Celebrity fashion analysis — red carpet or off-duty looks read as cultural statements
3. Iconic piece — the history and enduring value of a brand's signature item
4. Designer profile — a creative director's vision, references, and aesthetic philosophy
5. Season trend report — the key codes of luxury fashion this season, with specific looks
[Writing guidance]
- Treat fashion as culture, art, and philosophy — not just clothing
- Describe silhouette, fabric, colour palette, and construction with editorial precision
- For celebrity fashion: include context — the event, the styling team, the message
[Title examples]
- "Dior Haute Couture: Maria Grazia Chiuri's Portrait of Femininity, Revisited"
- "Zendaya's Red-Carpet Philosophy: Fashion as Storytelling"
""",

    "Living": COMMON_STYLE + """
[Topic] Luxury Living — Furniture, Tableware, Lighting, Objects
[Brands & categories]
- Furniture: Minotti, B&B Italia, Poltrona Frau, Cassina, Molteni&C, Knoll, De Sede
- Tableware: Hermès Maison, Christofle, Bernardaud, Ginori 1735, Meissen, Puiforcat
- Lighting: Flos, Louis Poulsen, Artemide, Apparatus Studio, Roll & Hill
- Objects & décor: Murano glassware, Trudon candles, art objects, bespoke ceramics
[Angle — choose one at random]
1. Brand portrait — heritage, artisanal process, signature collection
2. Space curation — how to compose a specific room at the luxury level
3. New collection or collaboration — a notable new release and the designer behind it
4. The art of the table — fine dining at home, from linen to crystal to silverware
[Writing guidance]
- Let the reader feel the weight of polished silver, the warmth of cashmere, the cool of marble
- Centre the sensory experience the object creates, not its product specifications
- Frame price as an investment in enduring beauty
[Title examples]
- "Minotti's 2025 Collection: The Italian Art of Living, Refined Once More"
- "Setting the Table: A Guide to the Fine Art of Home Dining with Christofle"
""",
}

# Weekly topic schedule (Monday = 0)
WEEKLY = {
    0: "Cars",
    1: "Travel",
    2: "Sports",
    3: "Cars",
    4: "Fashion",
    5: "Travel",
    6: "Living",
}

# ──────────────────────────────────────────
# Step 1: Generate post with Claude
# ──────────────────────────────────────────
def generate_post(topic: str) -> dict:
    prompt = PROMPTS[topic]

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-opus-4-6",
            "max_tokens": 2000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    response.raise_for_status()
    raw = response.json()["content"][0]["text"]

    # Extract META description
    meta = ""
    if "[META]" in raw and "[/META]" in raw:
        meta = raw.split("[META]")[1].split("[/META]")[0].strip()
        raw = raw.split("[META]")[0].strip()

    # Extract IMAGE keyword
    image_keyword = topic.lower()
    if "[IMAGE]" in raw and "[/IMAGE]" in raw:
        image_keyword = raw.split("[IMAGE]")[1].split("[/IMAGE]")[0].strip()
        raw = raw.split("[IMAGE]")[0].strip()

    # Separate title from body
    lines = raw.strip().split("\n")
    title = lines[0].replace("#", "").strip()
    content = "\n".join(lines[1:]).strip()

    # Fallback title if parsing fails
    if content.startswith("<h2>") or len(title) > 100:
        title = f"Luxury {topic} — {datetime.now().strftime('%B %d, %Y')}"
        content = raw

    print(f"✅ Post generated: {title}")
    print(f"🔍 Image keyword: {image_keyword}")
    return {"title": title, "content": content, "meta": meta, "image_keyword": image_keyword}

# ──────────────────────────────────────────
# Step 2: Build content with hero image
# ──────────────────────────────────────────
def build_content_with_image(content: str, image_keyword: str) -> str:
    """Fetch Unsplash image and prepend as hero image to content."""
    image = fetch_unsplash_image(image_keyword)

    if not image:
        print("⚠️ No image found, posting without image")
        return content

    hero_html = f"""<div style="margin-bottom: 32px;">
  <img src="{image['url']}"
       alt="{image['alt']}"
       style="width:100%; max-height:520px; object-fit:cover; display:block;" />
  <p style="font-size:11px; color:#888; margin-top:6px; text-align:right;">
    Photo by <a href="{image['photographer_url']}?utm_source=luxury_blog&utm_medium=referral" target="_blank" style="color:#888;">{image['photographer']}</a>
    on <a href="https://unsplash.com/?utm_source=luxury_blog&utm_medium=referral" target="_blank" style="color:#888;">Unsplash</a>
  </p>
</div>
"""
    print(f"✅ Image added: {image['url'][:60]}...")
    return hero_html + content

# ──────────────────────────────────────────
# Step 3: Publish to Blogger (OAuth2)
# ──────────────────────────────────────────
def post_to_blogger(title: str, content: str, topic: str, access_token: str):
    labels_map = {
        "Cars":    ["Luxury Cars", "Automotive", "Mercedes-Benz", "Porsche"],
        "Travel":  ["Luxury Travel", "Hotels", "Four Seasons", "Aman"],
        "Sports":  ["F1", "Tennis", "EPL", "La Liga", "Luxury Sports"],
        "Fashion": ["Fashion", "Fashion Week", "Luxury Fashion", "Style"],
        "Living":  ["Interior Design", "Living", "Luxury Living", "Home"],
    }

    url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    body = {
        "title": title,
        "content": content,
        "labels": labels_map.get(topic, [topic]),
    }

    res = requests.post(url, headers=headers, json=body)
    res.raise_for_status()
    result = res.json()
    print(f"✅ Published to Blogger: {result.get('url', '')}")
    return result

# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────
def main():
    weekday = datetime.now().weekday()
    topic = WEEKLY.get(weekday, random.choice(list(PROMPTS.keys())))
    print(f"📌 Today's topic: {topic} (weekday index: {weekday})")

    # Get fresh access token
    access_token = get_access_token()

    # Generate post
    post = generate_post(topic)

    # Add hero image
    content_with_image = build_content_with_image(post["content"], post["image_keyword"])

    # Publish
    post_to_blogger(post["title"], content_with_image, topic, access_token)

if __name__ == "__main__":
    main()
