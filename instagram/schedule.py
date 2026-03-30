from datetime import datetime
import pytz

# Monday=0, Tuesday=1, ..., Sunday=6
# Fashion: even days (Mon, Wed, Fri, Sun) → 0, 2, 4, 6
# Living:  odd days  (Tue, Thu, Sat)      → 1, 3, 5

# Format distribution (per week, 14 posts total):
# AM slot (KST 11:00) → always brand_story   (7/week, 50%)
# PM slot (KST 19:00) → lifestyle or top3
#   Mon/Wed/Fri/Sun PM → lifestyle            (4/week, 29%)
#   Tue/Thu/Sat PM    → top3                 (3/week, 21%)

KST = pytz.timezone("Asia/Seoul")

def get_post_config() -> dict:
    now = datetime.now(KST)
    weekday = now.weekday()
    hour = now.hour

    category = "fashion" if weekday % 2 == 0 else "living"

    if hour < 15:
        # AM slot → brand story
        post_format = "story"
    else:
        # PM slot → lifestyle (even days) / top3 (odd days)
        post_format = "lifestyle" if weekday % 2 == 0 else "top3"

    return {
        "category": category,
        "format": post_format,
        "timestamp": now.isoformat(),
    }


if __name__ == "__main__":
    config = get_post_config()
    print(config)
