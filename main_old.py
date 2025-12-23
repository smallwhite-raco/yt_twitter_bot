import os, requests, tweepy
from dotenv import load_dotenv
import json

load_dotenv()


YT_KEY = os.getenv("YOUTUBE_API_KEY")


def load_channels():
    with open("channels.json", "r", encoding="utf-8") as f:
        return json.load(f)

CHANNEL_IDS = load_channels()


auth = tweepy.OAuth1UserHandler(
    os.getenv("TWITTER_API_KEY"),
    os.getenv("TWITTER_API_SECRET"),
    os.getenv("TWITTER_ACCESS_TOKEN"),
    os.getenv("TWITTER_ACCESS_SECRET")
)
twitter = tweepy.API(auth)


#log
LOG_FILE = "processed_ids_log.json"


def load_log():
    if not os.path.exists(LOG_FILE):
        return {"videos": {}, "live": {}}
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def save_log(log_data):
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)

log_data = load_log()

# check live
def find_live_video(channel_id):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "eventType": "live",
        "type": "video",
        "key": YT_KEY
    }
    res = requests.get(url, params=params).json()
    items = res.get("items", [])
    if items:
        vid = items[0]["id"]["videoId"]
        title = items[0]["snippet"]["title"]
        return vid, title
    return None, None


def check_live():
    for cid, info in CHANNEL_IDS.items():
        vid, title = find_live_video(cid)
        if vid and log_data["live"].get(cid) != vid:
            link = f"https://www.youtube.com/watch?v={vid}"
            text = f" {info['name']} 配信中！\n{title}\n{link}\n{info['tag']}"
            try:
                tweet(text)
                log_data["live"][cid] = vid
                save_log(log_data)
            except Exception as e:
                print("Tweet Failed:", e)


# post twitter
def tweet(text):
    twitter.update_status(text)
