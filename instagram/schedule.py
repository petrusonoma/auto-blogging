from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")

def get_post_config() -> dict:
    now = datetime.now(KST)
    weekday = now.weekday()
    hour = now.hour

    category = "fashion" if weekday % 2 == 0 else "living"

    if hour < 15:
        # AM slot (fires at KST 09:00) → brand story
        post_format = "story"
    else:
        # PM slot (fires at KST 22:30) → lifestyle or top3
        post_format = "lifestyle" if weekday % 2 == 0 else "top3"

    return {
        "category": category,
        "format": post_format,
        "timestamp": now.isoformat(),
    }


if __name__ == "__main__":
    config = get_post_config()
    print(config)
