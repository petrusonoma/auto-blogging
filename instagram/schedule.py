from datetime import datetime
import pytz

# Monday=0, Tuesday=1, ..., Sunday=6
# Fashion: even days (Mon, Wed, Fri, Sun) → 0, 2, 4, 6
# Living:  odd days  (Tue, Thu, Sat)      → 1, 3, 5

KST = pytz.timezone("Asia/Seoul")

def get_post_config() -> dict:
    now = datetime.now(KST)
    weekday = now.weekday()
    hour = now.hour

    category = "fashion" if weekday % 2 == 0 else "living"

    # AM slot (cron fires at KST 11:00) → story
    # PM slot (cron fires at KST 19:00) → top3
    post_format = "story" if hour < 15 else "top3"

    return {
        "category": category,
        "format": post_format,
        "timestamp": now.isoformat(),
    }


if __name__ == "__main__":
    config = get_post_config()
    print(config)
