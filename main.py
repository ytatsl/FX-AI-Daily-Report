import os
import google.generativeai as genai
import requests
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 環境変数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Gemini初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# 3. チャンネル設定（RSSフィードURLを使用）
# YouTubeのRSSは "https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID" の形式
CHANNELS = [
    {
        "name": "竹内のりひろ（ガチプロFX）",
        "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCt8mRNDt9M0qC1QWunH660g", 
        "filter_type": "latest",
        "keywords": []
    },
    {
        "name": "FXトレードルーム（ひろぴー）",
        "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCbZt50s89QUHt96Yv6oT8Ew",
        "filter_type": "latest",
        "keywords": []
    },
    {
        "name": "ユーチェル（Yucheru）",
        "rss_url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCfQc4075b94k60_i1pM1jRQ",
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

def get_latest_video_from_rss(channel_conf):
    """RSSフィードから最新動画を取得（軽量・確実）"""
    print(f"Checking RSS: {channel_conf['name']}...")
    try:
        feed = feedparser.parse(channel_conf['rss_url'])
        
        if not feed.entries:
            print(f" -> 記事なし")
            return None

        # 最新の記事（動画）をチェック
        # RSSフィードは通常最新順に並んでいるので、上から順にチェック
        for entry in feed.entries[:3]:
            video_id = entry.yt_videoid
            title = entry.title
            link = entry.link
            
            # メンバー限定などのチェックはタイトルからは完全には分からないが、
            # 字幕取得時にエラーが出るのでそこで弾く
            
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
    """字幕取得（ここが最後の砦）"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:20000]
    except Exception:
        # 自動生成字幕にトライ
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
    print("=== RSS版 動画監視スタート ===")
    processed_ids = load_processed_ids()
    new_videos_found = False

    for ch in CHANNELS:
        video = get_latest_video_from_rss(ch)
        
        if not video:
            continue
            
        if video['id'] in processed_ids:
            print(f" -> Skip (既読): {video['title']}")
            continue

        print(f"★ New Video Hit: {video['title']}")
        transcript = get_transcript_text(video['id'])
        
        if not transcript:
            print(" -> ❌ 字幕取得失敗（メンバー限定か、字幕オフの可能性）")
            # 字幕が取れない場合も「既読」にしておかないと毎回トライしてしまうため、
            # ここでsaveするかは運用次第だが、今回はsaveせず再トライさせる（いつか字幕つくかも）
            continue

        # AI分析（NotebookLMの要約機能を再現）
        prompt = f"""
        あなたはプロのFXストラテジストです。
        以下のYouTube動画（{video['author']}）の内容を、NotebookLMのように高精度に要約してください。
        
        ■ 動画タイトル: {video['title']}
        ■ 動画の内容（字幕）:
        {transcript}

        ■ レポート作成指示
        1. **要点速報**: 相場の変動要因と結論を3行で。
        2. **トレード戦略**: 具体的に「どの通貨ペア」を「どの価格」で「どうする（ロング/ショート）」か。
        3. **プロの知見**: 金利、オプション、機関投資家の動向など、素人が気づかないポイント。
        
        ■ 出力形式
        【速報】{video['author']}の最新分析📺
        ━━━━━━━━━━━━
        Title: {video['title']}
        URL: {video['url']}
        
        【1】要点サマリ🌍
        (要約)
        
        【2】トレード戦略💰
        (戦略)
        
        【3】プロの知見📊
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
