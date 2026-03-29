import anthropic
import json
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

STORY_SYSTEM = """You are a creative director writing scripts for Instagram Reels 
targeting women in their 30s and above who appreciate quiet luxury. 
Your writing is like a literary magazine — evocative, restrained, never promotional.
Never use emoji. Never use exclamation marks. Never name-drop without context.
Always respond in valid JSON only. No markdown, no preamble."""

TOP3_SYSTEM = """You are a knowledgeable friend who has exquisite taste in luxury goods.
You write short, confident recommendations — like a private note, not a listicle.
Never use emoji. Keep the tone warm but authoritative.
Always respond in valid JSON only. No markdown, no preamble."""

STORY_PROMPT = """Category: {category}

Write an Instagram Reel script about a luxury {category} brand.
Choose a real, well-regarded brand with a compelling story (heritage, craft, or philosophy).
Do NOT write a product review. Write an emotional narrative — the soul of the brand.

Return this exact JSON structure:
{{
  "brand": "Brand Name",
  "scenes": [
    {{"duration": 4, "visual_hint": "brief description for image search", "overlay_text": "one sentence, lowercase, max 8 words"}},
    {{"duration": 4, "visual_hint": "brief description for image search", "overlay_text": "one sentence, lowercase, max 8 words"}},
    {{"duration": 4, "visual_hint": "brief description for image search", "overlay_text": "one sentence, lowercase, max 8 words"}}
  ],
  "caption": "English only. Under 150 words. Soft, literary tone. No emoji. No hashtags here.",
  "hashtags": ["niche_luxury_tag1", "niche_luxury_tag2", "niche_luxury_tag3", "niche_luxury_tag4", "niche_luxury_tag5"],
  "unsplash_queries": ["query1 for mood image", "query2 for mood image", "query3 for mood image"]
}}"""

TOP3_PROMPT = """Category: {category}

Write a self-Q&A Instagram Reel script recommending 3 luxury {category} brands.
Open with one quiet, rhetorical question. Answer with 3 brands — one line each, reason only.
Tone: a well-read friend sharing a private recommendation list.

Return this exact JSON structure:
{{
  "opening_question": "one rhetorical question, lowercase, ends with ?",
  "brands": [
    {{"name": "Brand Name", "reason": "one sentence, why it belongs here"}},
    {{"name": "Brand Name", "reason": "one sentence, why it belongs here"}},
    {{"name": "Brand Name", "reason": "one sentence, why it belongs here"}}
  ],
  "scenes": [
    {{"duration": 3, "visual_hint": "brief description for image search", "overlay_text": "one line, lowercase"}},
    {{"duration": 3, "visual_hint": "brief description for image search", "overlay_text": "one line, lowercase"}},
    {{"duration": 3, "visual_hint": "brief description for image search", "overlay_text": "one line, lowercase"}},
    {{"duration": 3, "visual_hint": "brief description for image search", "overlay_text": "one line, lowercase"}}
  ],
  "caption": "English only. Under 150 words. Start with the opening question. No emoji. No hashtags here.",
  "hashtags": ["niche_luxury_tag1", "niche_luxury_tag2", "niche_luxury_tag3", "niche_luxury_tag4", "niche_luxury_tag5"],
  "unsplash_queries": ["query1 for mood image", "query2 for mood image", "query3 for mood image"]
}}"""


def generate_script(category: str, post_format: str) -> dict:
    if post_format == "story":
        system = STORY_SYSTEM
        prompt = STORY_PROMPT.format(category=category)
    else:
        system = TOP3_SYSTEM
        prompt = TOP3_PROMPT.format(category=category)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    return json.loads(raw)


if __name__ == "__main__":
    result = generate_script("fashion", "story")
    print(json.dumps(result, indent=2))
