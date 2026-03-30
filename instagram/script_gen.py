import anthropic
import json
import os
import random
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

BASE_DIR = Path(__file__).parent
BRANDS_FILE = BASE_DIR / "brands.json"

# 70% chance to use brand pool, 30% Claude free choice
BRAND_POOL_RATIO = 0.7

STORY_SYSTEM = """You are a creative director writing scripts for Instagram Reels 
targeting women in their 30s and above who appreciate quiet luxury.
Your writing is like a literary magazine — evocative, precise, never promotional.
You know the deep history and craft behind every luxury brand.
Never use hollow superlatives. Let the story do the work.
Always respond in valid JSON only. No markdown, no preamble."""

TOP3_SYSTEM = """You are a knowledgeable friend with exquisite taste in luxury goods.
You write short, confident recommendations — like a private note, not a listicle.
Never use hollow superlatives. Keep the tone warm but authoritative.
Always respond in valid JSON only. No markdown, no preamble."""

STORY_PROMPT = """Category: {category}
Brand: {brand}

Write an Instagram Reel script about {brand}.
Do NOT write a product review. Write an emotional narrative — the heritage, craft, or defining moment that made this brand what it is.

Return this exact JSON structure:
{{
  "brand": "{brand}",
  "scenes": [
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "hook line, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "one phrase, lowercase, max 5 words"}},
    {{"duration": 3, "visual_hint": "specific visual for image search", "overlay_text": "closing phrase, lowercase, max 5 words"}}
  ],
  "caption": {{
    "hook": "One compelling question or surprising fact about {brand}. Max 2 sentences. Can include 1-2 relevant emoji.",
    "story": "The narrative. 3-5 sentences. The defining moment, the craft, the heritage. No emoji. English only.",
    "question": "One engagement question inviting the reader to reflect or share. 1 sentence. Can include 1 emoji."
  }},
  "hashtags": [
    "brand_specific_tag",
    "quietluxury",
    "category_relevant_tag1",
    "category_relevant_tag2",
    "category_relevant_tag3",
    "lifestyle_tag1",
    "lifestyle_tag2",
    "lifestyle_tag3",
    "aesthetic_tag1",
    "aesthetic_tag2",
    "niche_tag1",
    "niche_tag2",
    "niche_tag3",
    "niche_tag4"
  ],
  "unsplash_queries": ["query1 for mood image", "query2 for mood image", "query3 for mood image"]
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
    "brand1_tag",
    "brand2_tag",
    "brand3_tag",
    "quietluxury",
    "category_relevant_tag1",
    "category_relevant_tag2",
    "lifestyle_tag1",
    "lifestyle_tag2",
    "aesthetic_tag1",
    "aesthetic_tag2",
    "niche_tag1",
    "niche_tag2",
    "niche_tag3",
    "niche_tag4"
  ],
  "unsplash_queries": ["query1 for mood image", "query2 for mood image", "query3 for mood image"]
}}"""


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


def generate_script(category: str, post_format: str) -> dict:
    brand = _select_brand(category)

    if post_format == "story":
        brand_name = brand if brand else f"a remarkable {category} brand of your choice"
        prompt = STORY_PROMPT.format(category=category, brand=brand_name)
        system = STORY_SYSTEM
    else:
        pool = _load_brands().get(category, [])
        if pool:
            sample = random.sample(pool, min(3, len(pool)))
            brand_context = f"Consider featuring some of these: {', '.join(sample)}"
        else:
            brand_context = "Choose well-regarded luxury brands"
        prompt = TOP3_PROMPT.format(category=category, brand_context=brand_context)
        system = TOP3_SYSTEM

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
    raw = raw.strip()

    result = json.loads(raw)

    if isinstance(result.get("caption"), dict):
        result["caption"] = _build_caption(result["caption"])

    return result


if __name__ == "__main__":
    result = generate_script("living", "story")
    print(json.dumps(result, indent=2))
