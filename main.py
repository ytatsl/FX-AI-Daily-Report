import os
import google.generativeai as genai
import requests
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Gemini初期化 (ご指定の 3-Flash に変更)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. チャンネル設定（ガチプロ仕様）
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
        "url": "https://www.youtube.com/@fx-yucheru/videos",
        "filter_type": "smart_select",
        "exclude": ["初心者", "手法", "メンタル", "対談", "勉強", "マインド"],
        "include": ["展望", "分析", "ファンダ", "週明け", "来週", "雇用統計", "CPI", "FOMC"]
    }
]

# 記憶ファイルの名前
HISTORY_FILE = "processed_videos.txt"

def load_processed_ids():
    """過去に通知済みの動画IDを読み込む"""
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return f.read().splitlines()

def save_processed_id(video_id):
    """通知した動画IDを記録する"""
    with open(HISTORY_FILE, "a") as f:
        f.write(video_id + "\n")

def get_video_info(channel_conf):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 5, # 最新5件からチェック
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_conf['url'], download=False)
            if 'entries' not in info: return None

            for video in info['entries']:
                title = video['title']
                video_id = video['id']
                
                # フィルタリングロジック
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
        except Exception:
            return None

def get_transcript_text(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:20000]
    except Exception:
        return None

def send_line(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": text}] }
    requests.post(url, headers=headers, json=payload)

def main():
    print("動画チェック開始...")
    processed_ids = load_processed_ids()
    new_videos_found = False

    for ch in CHANNELS:
        video = get_video_info(ch)
        
        # 動画が見つからない、または既に通知済みならスキップ
        if not video: continue
        if video['id'] in processed_ids:
            print(f"Skip (既読): {video['title']}")
            continue

        print(f"★ New Video: {video['title']}")
        transcript = get_transcript_text(video['id'])
        
        if not transcript:
            print("字幕取得失敗のためスキップ")
            continue

        # --- ここからGemini分析 ---
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
        (ここに要約)
        
        【2】トレード戦略💰
        (ここに戦略)
        
        【3】プロの視点📊
        (ここに重要発言)
        """
        
        try:
            response = model.generate_content(prompt)
            report_text = response.text
            
            # LINE送信
            send_line(report_text)
            
            # 「送ったよ」と記録する
            save_processed_id(video['id'])
            new_videos_found = True
            
        except Exception as e:
            print(f"Gemini Error: {e}")

    if not new_videos_found:
        print("新しい動画はありませんでした。")

if __name__ == "__main__":
    main()
