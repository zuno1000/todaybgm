#!/usr/bin/env python3
"""songs.json 更新スクリプト(曲カタログの自動拡充・死活チェック)

やること:
  1. 既存エントリの死活チェック → 再生不能になった動画をカタログから削除
  2. scripts/queries.json のジャンル別クエリで新曲を検索し、
     埋め込み可・再生時間を検証したうえで songs.json に追記

動作モード(自動判定):
  - 環境変数 YOUTUBE_API_KEY があれば YouTube Data API v3 を使用(GitHub Actions想定)
  - なければ検索結果ページ・watchページのスクレイピングで動作(ローカル想定)

新規追加の収録条件:
  - 埋め込み許可されている(embeddable / playableInEmbed)
  - ライブ配信ではない(配信は中断・ID変更で壊れやすいため自動追加しない)
  - 再生時間 8分以上(作業用BGMとしてのノイズ除去)
  - タイトルに除外キーワード(reaction, gameplay 等)を含まない

使い方:
  python scripts/update_songs.py [--max-per-genre 40] [--per-query 12] [--dry-run]
"""

import argparse
import concurrent.futures
import html
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS_PATH = os.path.join(ROOT, "songs.json")
QUERIES_PATH = os.path.join(ROOT, "scripts", "queries.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

MIN_SECONDS = 8 * 60          # 8分未満は自動追加しない
TITLE_BLOCKLIST = re.compile(
    r"reaction|gameplay|walkthrough|let'?s play|tutorial|review|trailer|"
    r"podcast|interview|shorts|episode \d|実況|解説|考察|ランキング",
    re.IGNORECASE)

MOOD_RULES = [
    (re.compile(r"rain|thunder|storm|雨|雷", re.I), "rain"),
    (re.compile(r"night|midnight|1 ?a\.?m|evening|夜", re.I), "night"),
    (re.compile(r"morning|sunrise|coffee|朝", re.I), "morning"),
    (re.compile(r"study|work|focus|concentrat|勉強|作業|集中", re.I), "focus"),
    (re.compile(r"sleep|relax|calm|peaceful|chill|healing|癒し|リラックス", re.I), "calm"),
    (re.compile(r"epic|orchestra|symphony", re.I), "epic"),
    (re.compile(r"fantasy|ethereal|enchant|magical|dreamy|mystic|幻想", re.I), "fantasy"),
    (re.compile(r"kawaii|cute|かわいい", re.I), "morning"),
    (re.compile(r"\bedm\b|house|electro|dance|future bass", re.I), "focus"),
]


class RateLimited(Exception):
    pass


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.8,ja;q=0.6",
        "Cookie": "CONSENT=YES+1",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return res.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimited(url) from e
        raise


# YouTubeへのスクレイピングはレート制限(429)されやすいので、
# 全スレッド共有のバックオフ+リクエスト間ジッターで礼儀正しく叩く
_backoff_until = 0.0
_backoff_lock = threading.Lock()


def polite_fetch(url, timeout=20, retries=8):
    global _backoff_until
    for attempt in range(retries):
        wait = _backoff_until - time.time()
        if wait > 0:
            time.sleep(wait)
        time.sleep(random.uniform(1.0, 2.0))
        try:
            return fetch(url, timeout)
        except RateLimited:
            with _backoff_lock:
                if time.time() >= _backoff_until:
                    _backoff_until = time.time() + 90
                    print("  429 rate limited — backing off 90s", flush=True)
        except Exception:
            if attempt >= retries - 1:
                raise
            time.sleep(2)
    raise RateLimited(url)


def duration_class(minutes):
    if minutes <= 30:
        return "short"
    if minutes <= 60:
        return "medium"
    return "long"


def guess_moods(title):
    moods = [m for pat, m in MOOD_RULES if pat.search(title)]
    return list(dict.fromkeys(moods))[:2]


# ---------------- スクレイピングモード ----------------

def scrape_search_ids(query, limit):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    page = polite_fetch(url)
    ids = re.findall(r'"videoId":"([\w-]{11})"', page)
    return list(dict.fromkeys(ids))[:limit]


def scrape_verify(video_id):
    """watchページから {title, seconds, live, embeddable, playable} を取得。取得失敗は None。"""
    try:
        page = polite_fetch(f"https://www.youtube.com/watch?v={video_id}&hl=en")
    except Exception:
        return None
    status = re.search(r'"playabilityStatus":\s*\{"status":"(\w+)"', page)
    emb = re.search(r'"playableInEmbed":(true|false)', page)
    live = re.search(r'"isLiveContent":(true|false)', page)
    secs = re.search(r'"lengthSeconds":"(\d+)"', page)
    title = re.search(r'<meta property="og:title" content="([^"]*)"', page)
    if not status:
        return None
    return {
        "id": video_id,
        "playable": status.group(1) == "OK",
        "embeddable": bool(emb) and emb.group(1) == "true",
        "live": bool(live) and live.group(1) == "true",
        "seconds": int(secs.group(1)) if secs else 0,
        "title": html.unescape(title.group(1)) if title else "",
    }


# ---------------- Data API モード ----------------

API_BASE = "https://www.googleapis.com/youtube/v3"


def api_get(endpoint, params, key):
    params = dict(params, key=key)
    url = f"{API_BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    return json.loads(fetch(url))


def api_search_ids(query, limit, key):
    data = api_get("search", {
        "part": "id", "type": "video", "videoEmbeddable": "true",
        "q": query, "maxResults": min(limit, 50), "safeSearch": "none",
    }, key)
    return [it["id"]["videoId"] for it in data.get("items", [])]


def parse_iso8601_duration(s):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", s or "")
    if not m:
        return 0
    h, mi, se = (int(x) if x else 0 for x in m.groups())
    return h * 3600 + mi * 60 + se


def api_verify_batch(video_ids, key):
    """videos.list で一括検証。返り値は {id: info}。APIに存在しないIDは playable=False。"""
    out = {vid: {"id": vid, "playable": False, "embeddable": False,
                 "live": False, "seconds": 0, "title": ""} for vid in video_ids}
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        data = api_get("videos", {
            "part": "snippet,contentDetails,status",
            "id": ",".join(chunk), "maxResults": 50,
        }, key)
        for it in data.get("items", []):
            vid = it["id"]
            out[vid] = {
                "id": vid,
                "playable": True,
                "embeddable": it.get("status", {}).get("embeddable", False),
                "live": it.get("snippet", {}).get("liveBroadcastContent", "none") != "none",
                "seconds": parse_iso8601_duration(
                    it.get("contentDetails", {}).get("duration", "")),
                "title": it.get("snippet", {}).get("title", ""),
            }
    return out


# ---------------- メイン処理 ----------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-genre", type=int, default=40,
                    help="ジャンルごとのカタログ上限(第1ジャンル基準)")
    ap.add_argument("--per-query", type=int, default=12,
                    help="1クエリあたりの候補取得数")
    ap.add_argument("--dry-run", action="store_true", help="songs.json を書き換えない")
    args = ap.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    mode = "api" if api_key else "scrape"
    print(f"mode: {mode}")

    with open(SONGS_PATH, encoding="utf-8") as f:
        songs = json.load(f)
    with open(QUERIES_PATH, encoding="utf-8") as f:
        queries = json.load(f)

    known_ids = {s["id"] for s in songs}

    # ---- 1. 既存エントリの死活チェック ----
    print(f"checking {len(songs)} existing entries...")
    if mode == "api":
        infos = api_verify_batch([s["id"] for s in songs], api_key)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            results = list(ex.map(scrape_verify, [s["id"] for s in songs]))
        infos = {r["id"]: r for r in results if r}

    removed = []
    kept = []
    for s in songs:
        info = infos.get(s["id"])
        if info is None:
            kept.append(s)  # 取得失敗(ネットワーク等)は消さない
            continue
        if info["playable"] and info["embeddable"]:
            kept.append(s)
        else:
            removed.append(s)
    songs = kept
    for s in removed:
        print(f"  REMOVED (dead): {s['id']} {s['title']}")

    # ---- 2. 新曲の検索・検証・追加 ----
    genre_count = {}
    for s in songs:
        g = s["genres"][0]
        genre_count[g] = genre_count.get(g, 0) + 1

    added = []
    for genre, qs in queries.items():
        room = args.max_per_genre - genre_count.get(genre, 0)
        if room <= 0:
            print(f"[{genre}] full ({genre_count.get(genre, 0)}), skip")
            continue
        # 候補収集
        candidate_ids = []
        for q in qs:
            try:
                ids = (api_search_ids(q, args.per_query, api_key) if mode == "api"
                       else scrape_search_ids(q, args.per_query))
            except Exception as e:
                print(f"[{genre}] search failed '{q}': {e}")
                continue
            candidate_ids.extend(ids)
        candidate_ids = [v for v in dict.fromkeys(candidate_ids) if v not in known_ids]

        # 検証
        if mode == "api":
            infos = api_verify_batch(candidate_ids, api_key)
            verified = [infos[v] for v in candidate_ids]
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                verified = list(ex.map(scrape_verify, candidate_ids))

        n_added = 0
        for info in verified:
            if n_added >= room:
                break
            if not info or not info["playable"] or not info["embeddable"]:
                continue
            if info["live"] or info["seconds"] < MIN_SECONDS:
                continue
            if not info["title"] or TITLE_BLOCKLIST.search(info["title"]):
                continue
            minutes = round(info["seconds"] / 60)
            entry = {
                "id": info["id"],
                "title": info["title"][:80],
                "genres": [genre],
                "durationMin": minutes,
                "durationClass": duration_class(minutes),
                "mood": guess_moods(info["title"]),
            }
            songs.append(entry)
            known_ids.add(info["id"])
            added.append(entry)
            n_added += 1
        genre_count[genre] = genre_count.get(genre, 0) + n_added
        print(f"[{genre}] +{n_added} (total {genre_count[genre]})")

    # ---- 3. 保存 ----
    print(f"\nresult: {len(songs)} songs "
          f"(+{len(added)} added, -{len(removed)} removed)")
    if args.dry_run:
        print("dry-run: songs.json not written")
        return
    order = list(queries.keys())
    songs.sort(key=lambda s: (order.index(s["genres"][0])
                              if s["genres"][0] in order else 99, s["id"]))
    with open(SONGS_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {SONGS_PATH}")


if __name__ == "__main__":
    sys.exit(main())
