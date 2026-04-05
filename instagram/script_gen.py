import anthropic
import json
import os
import random
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

BASE_DIR = Path(__file__).parent
BRANDS_FILE = BASE_DIR / "brands.json"

BRAND_POOL_RATIO = 0.7

# ── System prompts ────────────────────────────────────────────────────────────

STORY_SYSTEM = """You are a creative director writing scripts for Instagram Reels
targeting women in their 30s and above who appreciate quiet luxury.
Your writing is sharp, specific, and surprising — like a great magazine sidebar.
Your job is to answer one question: why does this brand command the price it does?
Find the most unexpected, specific, lesser-known reason:
a historical turning point, a craft obsession, a founding decision that changed everything.
Lead with a hook that makes people stop scrolling.
Never use hollow superlatives. Let the facts do the work.
Always respond in valid JSON only. No markdown, no preamble."""

LIFESTYLE_SYSTEM = """You are a writer who understands that luxury is a mindset, not a price tag.
You pair beautiful images of spaces and fashion with quotes and ideas that make women
in their 30s and above feel seen, inspired, and elevated.
Your tone is quiet, confident, and deeply human — never preachy or motivational-poster generic.
The best quotes feel like something a brilliant friend whispered to you.
Always respond in valid JSON only. No markdown, no preamble."""

TOP3_SYSTEM = """You are a knowledgeable friend with exquisite taste in luxury goods.
You write short, confident recommendations — like a private note, not a listicle.
Never use hollow superlatives. Keep the tone warm but authoritative.
Always respond in valid JSON only. No markdown, no preamble."""

# ── Prompts ───────────────────────────────────────────────────────────────────

STORY_PROMPT = """Category: {category}
Brand: {brand}

Answer this question through storytelling: why does {brand} command the price it does?
Find the most surprising, specific, lesser-known angle —
a historical moment, a craft obsession, a founding decision, a royal connection, a near-death survival.
The hook must make someone stop scrolling. Think: "에르메스가 오렌지 박스를 쓰게 된 이유" energy.

Return this exact JSON structure:
{{
  "brand": "{brand}",
  "scenes": [
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "scroll-stopping hook, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "closing phrase, lowercase, max 5 words"}}
  ],
  "caption": {{
    "hook": "The most surprising fact or question about {brand}. Max 2 sentences. Make it impossible to ignore. Can include 1-2 relevant emoji.",
    "story": "The full narrative. 4-5 sentences. Specific facts, dates, names where possible. No emoji. English only.",
    "question": "One engagement question inviting reflection or personal connection. 1 sentence. Can include 1 emoji."
  }},
  "hashtags": [
    "STRATEGY: Mix these tiers — 2 large (5M+ posts), 6 medium (500K~5M posts), 6 niche (50K~500K posts). Prefer brand-specific, material-specific, era-specific, or craft-specific tags. AVOID overly broad tags like #handcrafted #minimalism #luxurylifestyle #interiordesign #homedecor. PREFER specific tags like #saintlouiscrystal #heirloompieces #frenchcraft #italianleather #porcelaintableware.",
    "brand_specific_tag",
    "quietluxury",
    "medium_tag1",
    "medium_tag2",
    "medium_tag3",
    "medium_tag4",
    "niche_tag1",
    "niche_tag2",
    "niche_tag3",
    "niche_tag4",
    "niche_tag5",
    "niche_tag6"
  ], = """Category: {category}

Write a lifestyle inspiration Instagram Reel pairing a beautiful {category} aesthetic
with a powerful quote or mindset that resonates with women in their 30s and above.

The quote should feel like something a brilliant, elegant woman would say —
not a generic poster quote. It can be from a real person (designer, writer, thinker)
or an original line in that spirit.

Examples of the right tone:
- "우아함은 거절하는 법을 아는 것에서 시작됩니다."
- "A beautiful room doesn't complete you. It reminds you of who you already are."
- "Buy less. Choose well. Make it last." — Vivienne Westwood

Return this exact JSON structure:
{{
  "quote": "The full quote in English",
  "quote_author": "Author name or 'anonymous' if original",
  "scenes": [
    {{"duration": 3, "visual_hint": "specific {category} aesthetic visual", "overlay_text": "first line of quote, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific {category} aesthetic visual", "overlay_text": "second line of quote, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific {category} aesthetic visual", "overlay_text": "third line or author, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific {category} aesthetic visual", "overlay_text": "closing thought, max 5 words"}}
  ],
  "caption": {{
    "hook": "Open with the quote or a question that makes it resonate. Max 2 sentences. Can include 1-2 relevant emoji.",
    "story": "2-3 sentences expanding on the mindset behind the quote. Soft, reflective tone. No emoji.",
    "question": "One gentle engagement question. 1 sentence. Can include 1 emoji."
  }},
  "hashtags": [
    "STRATEGY: 2 large tags (5M+ posts), 6 medium tags (500K~5M posts), 6 niche tags (50K~500K posts). AVOID: #luxurylifestyle #minimalism #homedecor #handcrafted. PREFER: quote-author-specific, mindset-specific, aesthetic-specific niche tags.",
    "quietluxury",
    "medium_mindset_tag1",
    "medium_mindset_tag2",
    "medium_aesthetic_tag1",
    "medium_aesthetic_tag2",
    "medium_category_tag1",
    "niche_tag1",
    "niche_tag2",
    "niche_tag3",
    "niche_tag4",
    "niche_tag5",
    "niche_tag6"
  ],
  "unsplash_queries": [
    "Translate the quote author into a mood/place/era search query — NOT the brand name itself. Examples: 'Coco Chanel' → 'paris atelier vintage fashion', 'Vivienne Westwood' → 'london fashion editorial bold', 'Georgia O Keeffe' → 'desert studio painter minimal', 'anonymous' → use {category} mood keywords like 'luxury interior soft light'. Generate 5 distinct queries this way.",
    "second translated mood/place/era query",
    "third translated mood/place/era query",
    "fourth translated mood/place/era query",
    "fifth translated mood/place/era query"
  ]
}}"""

TOP3_PROMPT = """Category: {category}
Brand context: {brand_context}

Write a self-Q&A Instagram Reel recommending 3 luxury {category} brands.
Open with one quiet, rhetorical question. Answer with 3 brands — one line each.
Tone: a well-read friend sharing a private recommendation.

Return this exact JSON structure:
{{
  "opening_question": "one rhetorical question, lowercase, ends with ?",
  "brands": [
    {{"name": "Brand Name", "reason": "one sentence, why it belongs here"}},
    {{"name": "Brand Name", "reason": "one sentence, why it belongs here"}},
    {{"name": "Brand Name", "reason": "one sentence, why it belongs here"}}
  ],
  "scenes": [
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}}
  ],
  "caption": {{
    "hook": "The opening rhetorical question expanded slightly. Max 2 sentences. Can include 1-2 relevant emoji.",
    "story": "Brief intro + 3 brand recommendations, each with one reason. No emoji. English only.",
    "question": "One engagement question. 1 sentence. Can include 1 emoji."
  }},
  "hashtags": [
    "STRATEGY: 2 large (5M+), 6 medium (500K~5M), 6 niche (50K~500K). AVOID: #luxurylifestyle #homedecor #handcrafted #minimalism. PREFER: brand-specific, material-specific, craft-specific niche tags.",
    "brand1_tag", "brand2_tag", "brand3_tag",
    "quietluxury",
    "medium_tag1", "medium_tag2",
    "medium_tag3", "medium_tag4",
    "niche_tag1", "niche_tag2", "niche_tag3", "niche_tag4"
  ],
  "unsplash_queries": ["query1 for mood image", "query2 for mood image", "query3 for mood image", "query4 for mood image", "query5 for mood image"]
}}"""

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_brands() -> dict:
    if BRANDS_FILE.exists():
        with open(BRANDS_FILE, "r") as f:
            return json.load(f)
    return {"fashion": [], "living": []}


def _select_brand(category: str) -> str | None:
    brands = _load_brands()
    pool = brands.get(category, [])
    if pool and random.random() < BRAND_POOL_RATIO:
        selected = random.choice(pool)
        print(f"  Brand (pool): {selected}")
        return selected
    print("  Brand: Claude free choice")
    return None


def _build_caption(caption_dict: dict) -> str:
    hook = caption_dict.get("hook", "")
    story = caption_dict.get("story", "")
    question = caption_dict.get("question", "")
    return f"{hook}\n\n{story}\n\n{question}"


def _call_claude(system: str, prompt: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


SCENARIOS_DIR = BASE_DIR / "scenarios"


def _delete_scenario_from_github(filename: str):
    """Delete scenario file from GitHub repo via API after use."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")  # auto-set by Actions: owner/repo
    if not token or not repo:
        print("  ⚠ GITHUB_TOKEN or GITHUB_REPOSITORY not set — skipping remote delete")
        return

    import urllib.request
    import urllib.error

    # Get file SHA (required for deletion)
    api_url = f"https://api.github.com/repos/{repo}/contents/instagram/scenarios/{filename}"
    req = urllib.request.Request(api_url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with urllib.request.urlopen(req) as res:
            sha = json.loads(res.read())["sha"]
    except Exception as e:
        print(f"  ⚠ Could not get file SHA: {e}")
        return

    # Delete file
    import json as _json
    delete_data = _json.dumps({
        "message": f"Remove used scenario: {filename}",
        "sha": sha
    }).encode()
    del_req = urllib.request.Request(api_url, data=delete_data, method="DELETE", headers={
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        urllib.request.urlopen(del_req)
        print(f"  ✓ Scenario deleted from GitHub: {filename}")
    except Exception as e:
        print(f"  ⚠ Could not delete from GitHub: {e}")


def _load_scenario() -> dict | None:
    """Check scenarios/ folder for pending JSON files. Use and delete the oldest one."""
    print(f"  Checking scenarios dir: {SCENARIOS_DIR}")
    if not SCENARIOS_DIR.exists():
        print(f"  ⚠ scenarios/ folder not found")
        return None
    files = sorted(SCENARIOS_DIR.glob("*.json"))
    print(f"  Found {len(files)} scenario file(s): {[f.name for f in files]}")
    if not files:
        return None
    path = files[0]
    with open(path, "r") as f:
        data = json.load(f)
    filename = path.name
    path.unlink()  # Delete local copy
    _delete_scenario_from_github(filename)  # Delete from GitHub repo
    print(f"  ✓ Using manual scenario: {filename}")
    return data


# ── Main ──────────────────────────────────────────────────────────────────────

def generate_script(category: str, post_format: str) -> dict:
    # Check for manual scenario first
    scenario = _load_scenario()
    if scenario:
        if isinstance(scenario.get("caption"), dict):
            scenario["caption"] = _build_caption(scenario["caption"])
        return scenario

    if post_format == "story":
        brand = _select_brand(category)
        brand_name = brand if brand else f"a remarkable {category} brand of your choice"
        result = _call_claude(STORY_SYSTEM, STORY_PROMPT.format(category=category, brand=brand_name))

    elif post_format == "lifestyle":
        result = _call_claude(LIFESTYLE_SYSTEM, LIFESTYLE_PROMPT.format(category=category))

    else:  # top3
        pool = _load_brands().get(category, [])
        if pool:
            sample = random.sample(pool, min(3, len(pool)))
            brand_context = f"Consider featuring some of these: {', '.join(sample)}"
        else:
            brand_context = "Choose well-regarded luxury brands"
        result = _call_claude(TOP3_SYSTEM, TOP3_PROMPT.format(category=category, brand_context=brand_context))

    # Flatten caption dict → single string
    if isinstance(result.get("caption"), dict):
        result["caption"] = _build_caption(result["caption"])

    return result


if __name__ == "__main__":
    result = generate_script("living", "lifestyle")
    print(json.dumps(result, indent=2))
