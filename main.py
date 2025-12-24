import os, requests, tweepy, feedparser, json
from dotenv import load_dotenv

load_dotenv()


YT_KEY = os.getenv("YOUTUBE_API_KEY")


def load_channels():
    with open("channels.json", "r", encoding="utf-8") as f:
        return json.load(f)

CHANNEL_IDS = load_channels()


client = tweepy.Client(
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET")
)

#log
LOG_FILE = "processed_ids_log.json"

def load_log():
    if not os.path.exists(LOG_FILE):
        return {"videos": {}, "live": {}}
    with open(LOG_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"videos": {}, "live": {}}
    if "live" not in data:
        data["live"] = {}
    return data

def save_log(data):
    if "live" not in data:
        data["live"] = {}
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
        snippet = items[0]["snippet"]
        live_details = items[0].get("liveStreamingDetails", {})
        # print(f"[DEBUG] {video_id} | {snippet.get('title')} | "
        #       f"liveBroadcastContent={snippet.get('liveBroadcastContent')} | "
        #       f"liveStreamingDetails={live_details}")

        if snippet.get("liveBroadcastContent") == "live":
            return True
        if "actualStartTime" in live_details and "actualEndTime" not in live_details:
            return True
    return False


def check_live():
    any_live = False
    for cid, info in CHANNEL_IDS.items():
        vid, title = find_latest_video(cid)
        live_status = is_live(vid)
        print(f"[DEBUG] cid={cid}, vid={vid}, title={title}, is_live={live_status}, logged={log_data.get('live', {}).get(cid)}")
        if vid and live_status and log_data.get("live", {}).get(cid) != vid:
            link = f"https://www.youtube.com/watch?v={vid}"
            text = f"{info['name']} 配信中！\n{title}\n{link}\n{info['tag']}"
            try:
                client.create_tweet(text=text)
                log_data["live"][cid] = vid
                save_log(log_data)
                print(f"[INFO] Tweeted live: {info['name']} - {title}")
                any_live = True
            except Exception as e:
                print("[ERROR] Tweet Failed:", e)

    if not any_live:
        print("no one is streaming")


if __name__ == "__main__":
    check_live()
