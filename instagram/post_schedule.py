from datetime import datetime
import pytz

KST = pytz.timezone("Asia/Seoul")

# Schedule table:
# Weekday: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
#
# AM 09:00
# Mon: story/fashion, Tue: celebrity/fashion, Wed: story/fashion
# Thu: story/living,  Fri: story/fashion,    Sat: story/living, Sun: celebrity/fashion
#
# PM 22:30
# Mon: lifestyle/living, Tue: top3/fashion,    Wed: lifestyle/fashion
# Thu: top3/living,      Fri: lifestyle/fashion, Sat: celebrity/fashion, Sun: lifestyle/living

SCHEDULE = {
    0: {"am": ("story",     "fashion"), "pm": ("lifestyle", "living")},
    1: {"am": ("celebrity", "fashion"), "pm": ("top3",      "fashion")},
    2: {"am": ("story",     "fashion"), "pm": ("lifestyle", "fashion")},
    3: {"am": ("story",     "living"),  "pm": ("top3",      "living")},
    4: {"am": ("story",     "fashion"), "pm": ("lifestyle", "fashion")},
    5: {"am": ("story",     "living"),  "pm": ("celebrity", "fashion")},
    6: {"am": ("celebrity", "fashion"), "pm": ("lifestyle", "living")},
}


def get_post_config() -> dict:
    now = datetime.now(KST)
    weekday = now.weekday()
    hour = now.hour

    slot = "am" if hour < 15 else "pm"
    post_format, category = SCHEDULE[weekday][slot]

    return {
        "category": category,
        "format": post_format,
        "timestamp": now.isoformat(),
    }


if __name__ == "__main__":
    config = get_post_config()
    print(config)
