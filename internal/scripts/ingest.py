#!/usr/bin/env python3
"""
ConvergenceTerminal - Active RSS & Feed Ingestion Engine
Fetches real-time feeds from configured RSS/Atom anchors, parses clean summaries,
resolves canonical source URLs, and stages records in internal/data/raw_feeds.json.
"""

import sys
import json
import os
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import email.utils
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR)) if os.path.basename(os.path.dirname(SCRIPT_DIR)) == "internal" else os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
try:
    import db
    import pipeline
except ImportError:
    db = None
    pipeline = None

# Load .env if present
def load_dotenv(filepath=".env"):
    if not os.path.exists(filepath):
        parent_env = os.path.join(BASE_DIR, ".env")
        if os.path.exists(parent_env):
            filepath = parent_env
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v

load_dotenv()

RSS_FEEDS = [
    {
        "name": "Lyn Alden Newsletter",
        "url": "https://www.lynalden.com/feed/",
        "entity_name": "Lyn Alden",
        "handle": "@LynAldenContact",
        "category": "Macro Plumbing & Balance Sheets",
        "platform": "newsletter",
        "avatar_url": "https://unavatar.io/x/LynAldenContact",
        "velocity_hint": 9.0
    }
]

def get_twitter_api_key():
    return os.environ.get("TWITTER_API_KEY") or os.environ.get("TWITTERAPI_IO_KEY")

def load_watchlist():
    possible_paths = [
        os.path.join(BASE_DIR, "internal", "config", "crypto_twitter_watchlist.json"),
        os.path.join("internal", "config", "crypto_twitter_watchlist.json"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f).get("watchlist", [])
    return []

def strip_html_tags(text):
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"&[a-zA-Z0-9#]+;", " ", clean)
    return " ".join(clean.split()).strip()

def _local_tag(tag):
    return tag.split("}")[-1] if "}" in tag else tag

def parse_xml_feed(xml_content, feed_config):
    """
    Namespace-agnostic parser supporting both RSS 2.0 (<channel><item>) and Atom (<feed><entry>).
    """
    root = ET.fromstring(xml_content)
    items = []

    # Check for RSS 2.0
    channel = None
    for child in root:
        if _local_tag(child.tag) == "channel":
            channel = child
            break

    if channel is not None:
        for node in channel:
            if _local_tag(node.tag) == "item":
                title = ""
                link = ""
                desc = ""
                pub_date = ""
                for child in node:
                    ltag = _local_tag(child.tag)
                    if ltag == "title":
                        title = (child.text or "").strip()
                    elif ltag == "link":
                        link = (child.text or "").strip()
                    elif ltag in ["description", "encoded"]:
                        desc = child.text or desc
                    elif ltag in ["pubDate", "date"]:
                        pub_date = (child.text or "").strip()

                raw_text = strip_html_tags(f"{title}. {desc}" if desc else title)
                if len(raw_text) > 400:
                    raw_text = raw_text[:397] + "..."

                iso_pub_date = None
                if pub_date:
                    try:
                        parsed_dt = email.utils.parsedate_to_datetime(pub_date)
                        iso_pub_date = parsed_dt.astimezone(timezone.utc).isoformat()
                    except Exception:
                        iso_pub_date = pub_date

                if title or desc:
                    items.append({
                        "title": title,
                        "link": link,
                        "raw_text": raw_text,
                        "timestamp": iso_pub_date or datetime.now(timezone.utc).isoformat()
                    })
    else:
        # Atom feed
        for node in root:
            if _local_tag(node.tag) == "entry":
                title = ""
                link = ""
                content = ""
                updated = ""
                for child in node:
                    ltag = _local_tag(child.tag)
                    if ltag == "title":
                        title = (child.text or "").strip()
                    elif ltag == "link":
                        link = child.get("href", "") or (child.text or "").strip()
                    elif ltag in ["content", "summary"]:
                        content = child.text or content
                    elif ltag in ["updated", "published"]:
                        updated = (child.text or "").strip()

                raw_text = strip_html_tags(f"{title}. {content}" if content else title)
                if len(raw_text) > 400:
                    raw_text = raw_text[:397] + "..."

                if title or content:
                    items.append({
                        "title": title,
                        "link": link,
                        "raw_text": raw_text,
                        "timestamp": updated or datetime.now(timezone.utc).isoformat()
                    })

    # Format into standard internal post structure
    staged_records = []
    for idx, it in enumerate(items):
        raw_link = it["link"]
        if db and hasattr(db, "resolve_source_url"):
            resolved_link = db.resolve_source_url(raw_link, handle=feed_config["handle"], platform=feed_config["platform"])
        else:
            resolved_link = raw_link or feed_config["url"]

        staged_records.append({
            "id": f"rss_{feed_config['handle'].lstrip('@')}_{idx + 1}",
            "timestamp": it["timestamp"],
            "entity": {
                "name": feed_config["entity_name"],
                "handle": feed_config["handle"],
                "platform": feed_config["platform"],
                "avatar_url": feed_config["avatar_url"]
            },
            "source_url": resolved_link,
            "category": feed_config["category"],
            "raw_text": it["raw_text"],
            "velocity_hint": feed_config.get("velocity_hint", 8.0),
            "sparkline": [15, 24, 38, 55, 80, 115, 145]
        })

    return staged_records

def fetch_feed_data(feed_config, timeout=10):
    url = feed_config["url"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) ConvergenceTerminal/1.0"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        # No explicit SSL context — urllib uses the system default, which validates
        # certificates via the OS trust store. Never use ssl._create_unverified_context().
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read()
    except Exception as e:
        print(f"  ⚠️  [NETWORK WARN] Could not reach {feed_config['name']} ({url}): {e}")
        return None

def harvest_all_feeds():
    """
    Harvests all configured RSS anchors. Returns list of parsed records.
    """
    all_staged = []
    print("📡 Harvesting Configured RSS & Publication Anchors:")
    for f in RSS_FEEDS:
        print(f"  Fetching: {f['name']} -> {f['url']}")
        raw_xml = fetch_feed_data(f)
        if raw_xml:
            try:
                items = parse_xml_feed(raw_xml, f)
                print(f"  ✅ Parsed {len(items)} items from {f['name']}")
                all_staged.extend(items)
            except Exception as pe:
                print(f"  ❌ XML Parsing error for {f['name']}: {pe}")
        else:
            print(f"  ℹ️ Skipping offline/unreachable feed: {f['name']}")

    return all_staged

def fetch_user_tweets(clean_handle, api_key, limit=3, timeout=10):
    """
    Queries TwitterAPI.io user/last_tweets endpoint with retry & backoff.
    """
    import time
    url = f"https://api.twitterapi.io/twitter/user/last_tweets?userName={clean_handle}"
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "Mozilla/5.0 ConvergenceTerminal/1.0"
    }
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(2):
        try:
            # No explicit SSL context — uses the system default for proper TLS validation.
            with urllib.request.urlopen(req, timeout=timeout) as res:
                if res.status == 200:
                    payload = json.loads(res.read().decode("utf-8"))
                    tweets = payload.get("data", {}).get("tweets", [])
                    return tweets[:limit]
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                print(f" (429 backoff 3s)", end="", flush=True)
                time.sleep(3.0)
                continue
            return None
        except Exception:
            return None
    return None

def format_tweet_record(tweet, entity_meta):
    import time
    tweet_id = str(tweet.get("id", ""))
    clean_handle = entity_meta["handle"].lstrip("@")

    raw_text = tweet.get("text", "")
    text_clean = re.sub(r"https://t\.co/\w+$", "", raw_text).strip()
    if not text_clean:
        text_clean = raw_text

    likes = int(tweet.get("likeCount", 0) or 0)
    rts = int(tweet.get("retweetCount", 0) or 0)
    views = int(tweet.get("viewCount", 0) or 0)

    # Dynamic velocity scaling based on actual engagement
    engagement_points = (rts * 4) + (likes * 1) + (views // 1000)
    if engagement_points > 5000:
        velocity_score = 9.8
    elif engagement_points > 1000:
        velocity_score = 9.2
    elif engagement_points > 300:
        velocity_score = 8.6
    elif engagement_points > 50:
        velocity_score = 7.8
    else:
        velocity_score = entity_meta.get("velocity_hint", 7.5)

    base = max(10, int(velocity_score * 8))
    sparkline = [
        int(base * 0.4),
        int(base * 0.6),
        int(base * 0.5),
        int(base * 0.9),
        int(base * 1.3),
        int(base * 1.8),
        int(base * 2.4)
    ]

    source_url = tweet.get("twitterUrl") or tweet.get("url") or f"https://x.com/{clean_handle}/status/{tweet_id}"
    created_at = tweet.get("createdAt")
    iso_timestamp = None
    if created_at:
        try:
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            iso_timestamp = dt.isoformat()
        except Exception:
            iso_timestamp = datetime.now(timezone.utc).isoformat()
    else:
        iso_timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "id": f"tw_{clean_handle}_{tweet_id}",
        "timestamp": iso_timestamp,
        "entity": {
            "name": entity_meta.get("name", clean_handle),
            "handle": f"@{clean_handle}",
            "platform": "x",
            "avatar_url": f"https://unavatar.io/x/{clean_handle}"
        },
        "source_url": source_url,
        "category": entity_meta.get("category", "Macro Plumbing & Balance Sheets"),
        "raw_text": text_clean,
        "velocity_hint": round(velocity_score, 1),
        "sparkline": sparkline
    }

def harvest_twitter_relay(watchlist, api_key, max_accounts=8):
    """
    Fetches latest tweets across VIP accounts using developer relay.
    Paces requests with a 2-second sleep to respect relay rate limits.
    """
    import time
    if not api_key:
        return []

    print(f"\n🐦 Harvesting Live VIP Tweets from TwitterAPI.io Developer Relay:")
    staged_tweets = []
    # Prioritize Tier-1 VIP thinkers
    sorted_watchlist = sorted(watchlist, key=lambda x: 0 if x.get("priority") == "Tier-1" else 1)
    target_accounts = sorted_watchlist[:max_accounts]

    for meta in target_accounts:
        handle = meta["handle"].lstrip("@")
        print(f"  Fetching: @{handle} ({meta.get('name')})...", end="", flush=True)
        time.sleep(2.0)  # Rate limit pacing
        tweets = fetch_user_tweets(handle, api_key, limit=3)
        if tweets:
            count = 0
            for tw in tweets:
                record = format_tweet_record(tw, meta)
                if record["raw_text"]:
                    staged_tweets.append(record)
                    count += 1
            print(f" ✅ ({count} tweets)")
        else:
            print(f" ⚠️ (fallback to archive/baseline)")

    print(f"  Total live tweets harvested: {len(staged_tweets)}")
    return staged_tweets

def main():
    print("==================================================")
    print("⚡ ConvergenceTerminal: Active Ingest Pipeline")
    print("   Module: Active Ingestion Engine")
    print("==================================================")

    # 1. Check Developer Relay API Key
    api_key = get_twitter_api_key()
    if api_key:
        masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
        print(f"🔑 TwitterAPI.io Relay Key: Configured ({masked_key}) via .env")
    else:
        print("⚠️  TwitterAPI.io Relay Key: Not detected (Standard $0.00 RSS mode active)")

    # 2. Curated VIP Watchlist
    watchlist = load_watchlist()
    print(f"📋 Curated VIP Watchlist: {len(watchlist)} thinkers configured")

    # 3. Harvest Live Feeds
    all_staged = []

    # A) RSS Feeds
    rss_items = harvest_all_feeds()
    all_staged.extend(rss_items)

    # B) Live Twitter Relay Feeds
    if api_key:
        live_tweets = harvest_twitter_relay(watchlist, api_key, max_accounts=8)
        all_staged.extend(live_tweets)


    # 4. Save Staged Feeds
    raw_feeds_path = os.path.join(BASE_DIR, "internal", "data", "raw_feeds.json")
    os.makedirs(os.path.dirname(raw_feeds_path), exist_ok=True)

    with open(raw_feeds_path, "w", encoding="utf-8") as f:
        json.dump(all_staged, f, indent=2)
    print(f"\n💾 Staged {len(all_staged)} high-signal feed items to {raw_feeds_path}")

    # 5. Run Two-Stage Pipeline (Sludge Bouncer + Alden Synthesis)
    if pipeline:
        print("\n🔄 Running Two-Stage Pipeline (Sludge Bouncer + Alden Synthesis)...")
        pipeline.run_pipeline(raw_feeds_path)

    print("\n✅ Ingest execution finished.")

if __name__ == "__main__":
    main()
