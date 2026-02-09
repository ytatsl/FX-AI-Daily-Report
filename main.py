import os
import google.generativeai as genai
import requests
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 環境変数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Gemini初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. チャンネル設定
CHANNELS = [
    {
        "name": "竹内のりひろ（ガチプロFX）",
        "url": "https://www.youtube.com/@gachipro/videos", 
        "search_query": "竹内のりひろ FX", # バックアップ検索ワード
        "filter_type": "latest",
        "keywords": []
    },
    {
        "name": "FXトレードルーム（ひろぴー）",
        "url": "https://www.youtube.com/@FX-traderoom/videos",
        "search_query": "FXトレードルーム ひろぴー",
        "filter_type": "latest",
        "keywords": []
    },
    {
        "name": "ユーチェル（Yucheru）",
        "url": "https://www.youtube.com/@fx-yucheru/videos",
        "search_query": "ユーチェル FX",
        "filter_type": "smart_select",
        "exclude": ["初心者", "手法", "メンタル", "対談", "勉強", "マインド"],
        "include": ["展望", "分析", "ファンダ", "週明け", "来週", "雇用統計", "CPI", "FOMC"]
    }
]

HISTORY_FILE = "processed_videos.txt"

def load_processed_ids():
    if not os.path.exists(HISTORY_FILE): return []
    with open(HISTORY_FILE, "r") as f: return f.read().splitlines()

def save_processed_id(video_id):
    with open(HISTORY_FILE, "a") as f: f.write(video_id + "\n")

def get_video_from_search(query):
    """URLがダメな場合のバックアップ：検索から最新動画を探す"""
    print(f" -> 🔄 URLアクセス失敗。検索モードで再トライ: '{query}'")
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 3,
        'ignoreerrors': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            # ytsearch3: = 検索結果の上位3つを取得
            info = ydl.extract_info(f"ytsearch3:{query}", download=False)
            if 'entries' in info:
                return info['entries']
        except Exception as e:
            print(f" -> 検索も失敗: {e}")
    return []

def get_video_info(channel_conf):
    print(f"Checking: {channel_conf['name']}")
    
    # 1. まずは直接URLでトライ
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 5,
        'ignoreerrors': True,
    }
    
    entries = []
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_conf['url'], download=False)
            if info and 'entries' in info:
                entries = info['entries']
        except Exception:
            pass

    # 2. 失敗したら（entriesが空なら）検索機能でバックアップ
    if not entries:
        entries = get_video_from_search(channel_conf['search_query'])

    if not entries:
        print(f" -> ❌ 動画が見つかりませんでした")
        return None

    # 3. フィルタリング処理
    for video in entries:
        if not video: continue
        title = video.get('title', 'No Title')
        video_id = video.get('id')
        
        # メンバー限定スキップ
        if "メンバー" in title or "Member" in title:
            print(f" -> Skip (Member Only): {title}")
            continue

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
            return {"id": video_id, "title": title, "author": channel_conf['name']}
    
    return None

def get_transcript_text(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:20000]
    except:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
            full_text = " ".join([t['text'] for t in transcript_list])
            return full_text[:20000]
        except:
            return None

def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": text}] }
    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"LINE送信エラー: {e}")

def main():
    print("動画チェック開始...")
    processed_ids = load_processed_ids()
    new_videos_found = False

    for ch in CHANNELS:
        video = get_video_info(ch)
        
        if not video: continue
            
        if video['id'] in processed_ids:
            print(f" -> Skip (既読): {video['title']}")
            continue

        print(f"★ New Video Hit: {video['title']}")
        transcript = get_transcript_text(video['id'])
        
        if not transcript:
            print(" -> ❌ 字幕なしのためスキップ")
            continue

        # AI分析
        prompt = f"""
        あなたはプロのFXストラテジストです。
        以下のYouTube動画（{video['author']}）の字幕データを速報として要約してください。
        
        ■ 動画タイトル: {video['title']}
        ■ 字幕データ:
        {transcript}

        ■ 分析指示
        1. **要点速報**: 何が起きたのか、何が重要なのかを3行で。
        2. **トレード戦略**: 具体的に「売り」か「買い」か、注目レートはどこか。
        3. **重要発言**: 金利、機関投資家の動きなど、プロならではの視点を抽出。
        
        ■ 出力形式
        【速報】{video['author']}の最新分析📺
        ━━━━━━━━━━━━
        Title: {video['title']}
        URL: https://youtu.be/{video['id']}
        
        【1】要点サマリ🌍
        (要約)
        
        【2】トレード戦略💰
        (戦略)
        
        【3】プロの視点📊
        (重要発言)
        """
        
        try:
            print(" -> AI解析中...")
            response = model.generate_content(prompt)
            report_text = response.text
            send_line(report_text)
            save_processed_id(video['id'])
            new_videos_found = True
            print(" -> ✅ 送信完了！")
            
        except Exception as e:
            print(f"Gemini Error: {e}")

    if not new_videos_found:
        print("新しい未読動画はありませんでした。")

if __name__ == "__main__":
    main()
