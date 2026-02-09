import os
import datetime
import google.generativeai as genai
import requests
from yt_dlp import YoutubeDL
from youtube_transcript_api import YouTubeTranscriptApi

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Gemini初期化 (長文読解が得意なProモデル)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# 3. チャンネル設定（ガチプロ仕様）
# ※ URLはチャンネルのホームURL(@...)を指定しています。もし動かない場合はYouTubeでチャンネルを開き、URLを確認してください。
CHANNELS = [
    {
        "name": "竹内のりひろ（ガチプロFX）",
        "url": "https://www.youtube.com/@gachipro", # 竹内氏のチャンネルURL（要確認）
        "filter_type": "latest", # 彼の動画は全て市況分析なので最新を取得
        "keywords": []
    },
    {
        "name": "FXトレードルーム（ひろぴー）",
        "url": "https://www.youtube.com/@FX-traderoom", # ひろぴー氏のチャンネルURL（要確認）
        "filter_type": "latest", # 最新の相場解説を取得
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

def get_video_info(channel_conf):
    """チャンネルから条件に合う最新動画を検索"""
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'playlistend': 10, # 最新10件から探す
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_conf['url'], download=False)
            if 'entries' not in info:
                return None

            for video in info['entries']:
                title = video['title']
                video_id = video['id']
                
                # A. 竹内氏 & FXトレードルーム: 最新ならOK（ただしShort動画などは除外したい場合は秒数チェックが必要だが一旦タイトルで判断）
                if channel_conf['filter_type'] == 'latest':
                    # 明らかに市況に関係なさそうなタイトル（Shortsなど）を除外する簡易フィルタ
                    if "Shorts" in title or "ショート" in title:
                        continue
                    return {"id": video_id, "title": title, "author": channel_conf['name']}
                
                # B. スマート選別（ユーチェル氏用）
                elif channel_conf['filter_type'] == 'smart_select':
                    if any(ex in title for ex in channel_conf['exclude']):
                        continue
                    if any(inc in title for inc in channel_conf['include']) or "ドル" in title or "円" in title:
                        return {"id": video_id, "title": title, "author": channel_conf['name']}
            
            return None # 条件に合う動画なし
            
        except Exception as e:
            print(f"Error fetching {channel_conf['name']}: {e}")
            return None

def get_transcript_text(video_id):
    """動画の字幕データを取得"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        full_text = " ".join([t['text'] for t in transcript_list])
        return full_text[:20000] # プロの分析は長尺が多いので文字数制限を緩和
    except Exception:
        return "（字幕データ取得不可）"

def main():
    print("動画情報を取得中...")
    summaries = []
    
    for ch in CHANNELS:
        video = get_video_info(ch)
        if video:
            print(f"Hit: {video['title']} ({ch['name']})")
            transcript = get_transcript_text(video['id'])
            
            if transcript != "（字幕データ取得不可）":
                summaries.append(f"""
                ■ 発信者: {video['author']}
                ■ 動画タイトル: {video['title']}
                ■ URL: https://youtu.be/{video['id']}
                ■ 内容（字幕データ）:
                {transcript}
                --------------------------------------------------
                """)
            else:
                print(f"Skip: 字幕なし - {video['title']}")
        else:
            print(f"No matching video found for {ch['name']}")

    if not summaries:
        print("有効な動画が見つかりませんでした。")
        return

    # AIへの要約指示（ガチプロ仕様）
    all_transcripts = "\n".join(summaries)
    
    prompt = f"""
    あなたは機関投資家レベルの視点を持つプロのFXストラテジストです。
    以下の信頼できるプロトレーダー（元HSBCチーフディーラー竹内氏、ひろぴー氏、ユーチェル氏）の動画内容を統合し、
    個人トレーダー向けの最高品質の市況レポートを作成してください。

    ■ 入力データ（プロ達の発言）
    {all_transcripts}

    ■ 分析の視点（重要）
    1. **竹内氏（元HSBC）の視点**: 「金利動向」「オプションバリア」「機関投資家のフロー」に関する発言は最重要情報として扱ってください。彼の発言は市場の"背骨"となります。
    2. **FXトレードルーム（ひろぴー氏）の視点**: 実践的なトレード戦略、RCI等のテクニカル分析、ビットコインとの相関などを拾ってください。
    3. **ユーチェル氏の視点**: 大きなファンダメンタルズの流れや週明けの注目ポイントを補完してください。

    ■ 執筆ルール
    - エンタメ要素は不要。事実と戦略のみを抽出すること。
    - 3人の意見が一致している部分は「強いコンセンサス」として強調すること。
    - 逆に意見が割れている部分は、それぞれの根拠を併記すること。

    ■ 出力フォーマット
    【1】プロトレーダー市況総括🌍
    （3人の見解を統合した、現在の市場センチメントと方向感）

    【2】機関投資家の視点・ファンダメンタルズ📊
    （竹内氏の分析を中心とした、金利・オプション・需給の解説）

    【3】実践トレード戦略と注目ポイント💰
    （今日〜明日にかけて狙うべき価格帯、エントリーポイント、損切りライン）

    【4】参照動画リスト📺
    （タイトルとURLのみ）
    """

    print("AI解析中...")
    response = model.generate_content(prompt)
    report_text = response.text

    # LINE送信
    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
