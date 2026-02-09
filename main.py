import os
import re
import requests
import feedparser
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# --- 設定 ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
HISTORY_FILE = "processed_videos.txt"

# Gemini初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# チャンネル設定 (@handle形式のURLでOK)
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

def load_processed_ids():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_processed_id(video_id):
    with open(HISTORY_FILE, "a") as f: f.write(video_id + "\n")

def get_channel_id(url):
    """チャンネルURL(@handle)からID(UC...)を強制的に抜き出す"""
    try:
        # スマホのふりをしてアクセス（軽量）
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'}
        res = requests.get(url, headers=headers, timeout=10)
        
        # 複数のパターンでIDを探す
        patterns = [
            r'"channelId":"(UC[\w-]+)"',
            r'<meta itemprop="channelId" content="(UC[\w-]+)">',
            r'"externalId":"(UC[\w-]+)"',
            r'data-channel-id="(UC[\w-]+)"'
        ]
        
        for p in patterns:
            match = re.search(p, res.text)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        print(f"ID Search Error: {e}")
        return None

def get_latest_video(channel_conf):
    """IDを特定してからRSSで最新動画を取得"""
    print(f"Checking: {channel_conf['name']}...")
    
    # 1. チャンネルIDを特定
    cid = get_channel_id(channel_conf['url'])
    if not cid:
        print(f" -> ❌ ID特定失敗: {channel_conf['url']}")
        return None
        
    # 2. RSSで取得
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print(" -> RSS記事なし")
        return None

    # 3. 最新記事をチェック
    for entry in feed.entries[:3]:
        vid = entry.yt_videoid
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
            return {"id": vid, "title": title, "url": link, "author": channel_conf['name']}
            
    return None

def get_transcript(video_id):
    try:
        # 日本語字幕
        ts = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        return " ".join([t['text'] for t in ts])[:20000]
    except:
        try:
            # 英語などの自動翻訳字幕
            ts = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
            return " ".join([t['text'] for t in ts])[:20000]
        except:
            return None

def send_line(text):
    # ここでのエラーを防ぐため変数を明確に
    api_url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    try:
        requests.post(api_url, headers=headers, json=payload)
    except Exception as e:
        print(f"LINE Error: {e}")

def main():
    print("=== RSS Monitor Start ===")
    processed = load_processed_ids()
    hit = False

    for ch in CHANNELS:
        video = get_latest_video(ch)
        if not video: continue
        
        if video['id'] in processed:
            print(f" -> Skip (既読): {video['title']}")
            continue

        print(f"★ New Video: {video['title']}")
        transcript = get_transcript(video['id'])
        
        if not transcript:
            print(" -> ❌ 字幕なし")
            continue

        # プロンプト（NotebookLM風）
        prompt = f"""
        あなたはプロのFXストラテジストです。
        以下のYouTube動画（{video['author']}）の内容を、NotebookLMのように高精度に要約してください。
        
        Title: {video['title']}
        Transcript:
        {transcript}

        ■ 出力フォーマット
        【速報】{video['author']}の最新分析📺
        ━━━━━━━━━━━━
        Title: {video['title']}
        URL: {video['url']}
        
        【1】要点サマリ🌍
        (3行要約)
        
        【2】トレード戦略💰
        (通貨ペア・売買方向・価格)
        
        【3】プロの知見📊
        (金利・機関投資家動向など)
        """
        
        try:
            print(" -> AI解析中...")
            res = model.generate_content(prompt)
            send_line(res.text)
            save_processed_id(video['id'])
            hit = True
            print(" -> ✅ 送信完了")
        except Exception as e:
            print(f"Gemini Error: {e}")

    if not hit:
        print("新しい動画はありません")

if __name__ == "__main__":
    main()
