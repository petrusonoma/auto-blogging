from datetime import datetime
import pytz

# Monday=0, Tuesday=1, ..., Sunday=6
# Fashion: even days (Mon, Wed, Fri, Sun) → 0, 2, 4, 6
# Living:  odd days  (Tue, Thu, Sat)      → 1, 3, 5

# Format distribution (per week, 14 posts total):
# AM slot (PST 08:00) → always brand_story   (7/week, 50%)
# PM slot (PST 19:00) → lifestyle or top3
#   Mon/Wed/Fri/Sun PM → lifestyle            (4/week, 29%)
#   Tue/Thu/Sat PM    → top3                 (3/week, 21%)

PST = pytz.timezone("America/Los_Angeles")

def get_post_config() -> dict:
    now = datetime.now(PST)
    weekday = now.weekday()
    hour = now.hour

    category = "fashion" if weekday % 2 == 0 else "living"

    if hour < 14:
        # AM slot (fires at PST 08:00) → brand story
        post_format = "story"
    else:
        # PM slot (fires at PST 19:00) → lifestyle or top3
        post_format = "lifestyle" if weekday % 2 == 0 else "top3"

    return {
        "category": category,
        "format": post_format,
        "timestamp": now.isoformat(),
    }


if __name__ == "__main__":
    config = get_post_config()
    print(config)
