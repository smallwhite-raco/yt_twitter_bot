import os, requests, tweepy, feedparser, json
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
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"videos": {}, "live": {}}


def save_log(log_data):
    with open(LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=2)

log_data = load_log()

# check latest video id
def find_latest_video(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    if feed.entries:
        latest = feed.entries[0]
        vid = latest.yt_videoid
        title = latest.title
        return vid, title
    return None, None

# check streaming with YT API
def is_live(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,liveStreamingDetails",
        "id": video_id,
        "key": YT_KEY
    }
    res = requests.get(url, params=params).json()
    items = res.get("items", [])
    if items:
        live_details = items[0].get("liveStreamingDetails", {})
        if "actualStartTime" in live_details and "actualEndTime" not in live_details:
            return True
    return False


def check_live():
    for cid, info in CHANNEL_IDS.items():
        vid, title = find_latest_video(cid)
        if vid and is_live(vid) and log_data["live"].get(cid) != vid:
            link = f"https://www.youtube.com/watch?v={vid}"
            text = f"{info['name']} 配信中！\n{title}\n{link}\n{info['tag']}"
            try:
                twitter.update_status(text)
                log_data["live"][cid] = vid
                save_log(log_data)
            except Exception as e:
                print("Tweet Failed:", e)