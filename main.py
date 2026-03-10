import os
import json
import yaml
import feedparser
import requests
from datetime import datetime, timezone
from googleapiclient.discovery import build

SEEN_FILE = "seen.json"
CONFIG_FILE = "config.yaml"


def load_config():
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f)


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f, indent=2)


def matches_allowlist(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def post_to_slack(webhook_url, title, url, source, summary=None):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*<{url}|{title}>*\n_{source}_"
            }
        }
    ]
    if summary:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": summary}]
        })
    blocks.append({"type": "divider"})

    response = requests.post(webhook_url, json={"blocks": blocks})
    response.raise_for_status()


def process_rss(config, seen, webhook_url):
    keywords = config["keywords"]
    new_seen = set()

    for feed_url in config["sources"]["rss"]:
        feed = feedparser.parse(feed_url)
        feed_title = feed.feed.get("title", feed_url)

        for entry in feed.entries:
            uid = entry.get("id") or entry.get("link")
            if not uid or uid in seen:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = f"{title} {summary}"

            if not matches_allowlist(combined, keywords):
                continue

            print(f"[RSS] Posting: {title}")
            post_to_slack(webhook_url, title, entry.link, feed_title)
            new_seen.add(uid)

    return new_seen


def process_youtube(config, seen, webhook_url):
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("No YOUTUBE_API_KEY set, skipping YouTube.")
        return set()

    keywords = config["keywords"]
    new_seen = set()
    youtube = build("youtube", "v3", developerKey=api_key)

    for channel_id in config["sources"].get("youtube", []):
        # Get uploads playlist
        channel_resp = youtube.channels().list(
            part="contentDetails,snippet",
            id=channel_id
        ).execute()

        if not channel_resp["items"]:
            continue

        channel_name = channel_resp["items"][0]["snippet"]["title"]
        playlist_id = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Get latest videos
        playlist_resp = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=5
        ).execute()

        for item in playlist_resp["items"]:
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]
            uid = f"yt_{video_id}"

            if uid in seen:
                continue

            title = snippet.get("title", "")
            description = snippet.get("description", "")[:300]
            combined = f"{title} {description}"

            if not matches_allowlist(combined, keywords):
                continue

            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"[YouTube] Posting: {title}")
            post_to_slack(webhook_url, title, url, f"YouTube · {channel_name}")
            new_seen.add(uid)

    return new_seen


def main():
    config = load_config()
    seen = load_seen()
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]

    new_rss = process_rss(config, seen, webhook_url)
    new_yt = process_youtube(config, seen, webhook_url)

    updated = seen | new_rss | new_yt
    save_seen(updated)
    print(f"Done. Posted {len(new_rss)} RSS + {len(new_yt)} YouTube items.")


if __name__ == "__main__":
    main()
