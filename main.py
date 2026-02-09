import os
import re
import requests
import feedparser
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 環境変数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Gemini初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. チャンネル設定（URLは @handle のままでOK！）
CHANNELS = [
    {
        "name": "竹内のりひろ（ガチプロFX）",
        "url": "https://www.youtube.com/@gachipro",
        "filter_type": "latest",
        "keywords": []
    },
    {
        "name": "FXトレードルーム（ひろぴー）",
        "url": "https://www.youtube.com/@FX-traderoom",
        "filter_type": "latest",
        "keywords": []
    },
    {
        "name": "ユーチェル（Yucheru）",
        "url": "https://www.youtube.com/@fx-yucheru",
        "filter_type": "smart_select",
        "exclude": ["初心者", "手法", "メンタル", "対談", "勉強", "マインド", "Live"],
        "include": ["展望", "分析", "ファンダ", "週明け", "来週", "雇用統計", "CPI", "FOMC", "予想"]
    }
]

HISTORY_FILE = "processed_videos.txt"

def load_processed_ids():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_processed_id(video_id):
    with open(HISTORY_FILE, "a") as f: f.write(video_id + "\n")

def get_channel_id(url):
    """チャンネルURLから正しいID(UC...)をスクレイピングで取得"""
    try:
        # ブラウザのふりをしてアクセス
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        res = requests.get(url, headers=headers)
        
        # HTML内から channelId を探す
        match = re.search(r'"channelId":"(UC[\w-]+)"', res.text)
        if match:
            return match.group(1)
        
        # 別のパターン（metaタグ）も探す
        match_meta = re.search(r'<meta itemprop="channelId" content="(UC[\w-]+)">', res.text)
        if match_meta:
            return match_meta.group(1)
            
        return None
    except Exception as e:
        print(f"ID取得エラー: {e}")
        return None

def get_latest_video_from_rss(channel_conf):
    """RSSフィードから最新動画を取得"""
    print(f"Checking: {channel_conf['name']}...")
    
    # 1. まず正しいチャンネルIDを取得
    channel_id = get_channel_id(channel_conf['url'])
    if not channel_id:
        print(f" -> ❌ チャンネルID特定失敗")
        return None
        
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    
    try:
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            print(f" -> 記事なし (RSS取得成功だが空)")
            return None

        # 最新3件チェック
        for entry in feed.entries[:3]:
            video_id = entry.yt_videoid
            title = entry.title
            link = entry.link
            
            # フィルタリング
            is_match = False
            if channel_conf['filter_type'] == 'latest':
                if "Shorts" not in title and "ショート" not in title:
                    is_match = True
            elif channel_conf['filter_type'] == 'smart_select':
                if not any(ex in title for ex in channel_conf['exclude']):
                    if any(inc in title for inc in channel_conf['include']) or "ドル" in title or "円" in title:
                        is_match = True
            
            if is_match:
                return {"id": video_id, "title": title, "url": link, "author": channel_conf['name']}
        
        return None

    except Exception as e:
        print(f" -> RSS Error: {e}")
        return None

def get_transcript_text(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:20000]
    except Exception:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
            full_text = " ".join([t['text'] for t in transcript_list])
            return full_text[:20000]
        except:
            return None

def send_line(text):
    url = "
