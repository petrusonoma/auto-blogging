"""
post.py — Luxury Lifestyle Blog Auto-Posting Script
Runs via GitHub Actions twice daily.

Required GitHub Secrets:
  - ANTHROPIC_API_KEY
  - BLOGGER_CREDENTIALS  (Full Google service account JSON)
  - BLOG_ID              (Blogger blog ID)
"""

import os
import json
import random
import requests
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ──────────────────────────────────────────
# Load environment variables
# ──────────────────────────────────────────
ANTHROPIC_API_KEY   = os.environ["ANTHROPIC_API_KEY"]
BLOGGER_CREDENTIALS = json.loads(os.environ["BLOGGER_CREDENTIALS"])
BLOG_ID             = os.environ["BLOG_ID"]

# ──────────────────────────────────────────
# Common style guide (applied to all topics)
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
    """Call Claude API → returns {title, content, meta}"""
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

    # Separate title from body
    lines = raw.strip().split("\n")
    title = lines[0].replace("#", "").strip()
    content = "\n".join(lines[1:]).strip()

    # Fallback title if parsing fails
    if content.startswith("<h2>") or len(title) > 100:
        title = f"Luxury {topic} — {datetime.now().strftime('%B %d, %Y')}"
        content = raw

    print(f"✅ Post generated: {title}")
    return {"title": title, "content": content, "meta": meta}

# ──────────────────────────────────────────
# Step 2: Publish to Blogger
# ──────────────────────────────────────────
def post_to_blogger(title: str, content: str, topic: str):
    """Publish via Google Blogger API"""
    scopes = ["https://www.googleapis.com/auth/blogger"]
    creds = service_account.Credentials.from_service_account_info(
        BLOGGER_CREDENTIALS, scopes=scopes
    )
    service = build("blogger", "v3", credentials=creds)

    labels_map = {
        "Cars":    ["Luxury Cars", "Automotive", "Mercedes-Benz", "Porsche"],
        "Travel":  ["Luxury Travel", "Hotels", "Four Seasons", "Aman"],
        "Sports":  ["F1", "Tennis", "EPL", "La Liga", "Luxury Sports"],
        "Fashion": ["Fashion", "Fashion Week", "Luxury Fashion", "Style"],
        "Living":  ["Interior Design", "Living", "Luxury Living", "Home"],
    }

    body = {
        "title": title,
        "content": content,
        "labels": labels_map.get(topic, [topic]),
    }

    result = service.posts().insert(blogId=BLOG_ID, body=body, isDraft=False).execute()
    print(f"✅ Published to Blogger: {result.get('url', '')}")
    return result

# ──────────────────────────────────────────
# Main
# ──────────────────────────────────────────
def main():
    weekday = datetime.now().weekday()
    topic = WEEKLY.get(weekday, random.choice(list(PROMPTS.keys())))
    print(f"📌 Today's topic: {topic} (weekday index: {weekday})")

    post = generate_post(topic)
    post_to_blogger(post["title"], post["content"], topic)

if __name__ == "__main__":
    main()
