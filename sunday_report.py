import os
import datetime
import google.generativeai as genai
import requests

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Geminiの初期化 (最新の gemini-3-flash-preview を使用)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def main():
    # 実行時の正確な「年・月・日」を取得
    now = datetime.datetime.now()
    current_year = now.year
    today_str = now.strftime('%Y年%m月%d日')
    
    # 「来週」の期間を明示（月曜〜日曜）
    # 日曜日に実行することを想定し、1日後(月)〜7日後(日)を計算
    next_monday_dt = now + datetime.timedelta(days=1)
    next_sunday_dt = now + datetime.timedelta(days=7)
    
    monday_str = next_monday_dt.strftime('%m月%d日')
    sunday_str = next_sunday_dt.strftime('%m月%d日')
    calendar_range = f"{monday_str}〜{sunday_str}"

    # AIへの指示：嘘を排除し、徹底的に数値を拾わせる
    prompt = f"""
    【最優先：情報の真実性と定量的データの取得】
    本日は {today_str}（日曜日）です。
    {current_year}年の【{calendar_range}】に向けた「週刊為替ファンダメンタルズ・レポート」をプロとして執筆してください。
    
    ■ 厳命：データ取得の鉄則（捏造は厳禁）
    1. 主要指標（ISM、米雇用統計、CPI、中銀会合など）について、ロイター、ブルームバーグ、日経新聞等の最新ソースから、先週確定した数値を必ず【予想 vs 結果】の形式で引用してください。
    2. 数値が「データなし」となった場合は、必ず「発表延期」や「未実施」といった具体的理由を確認してください。安易に「なし」で済ませず、最新ニュースから事実を特定してください。
    3. 数値の捏造、存在しないイベントの作成、他年度の情報の混入は、アナリストとして致命的な失態とみなします。

    ■ 執筆ガイドライン
    💰 視認性：1行ごとに必ず絵文字（💰、📈、⚠️、📊等）を使用し、スクロールだけで要点がわかるようにしてください。
    📊 構成：見出しは「【1】見出し🌍」の形式、セクション区切りは「━━━━━━━━━━━━」。
    🌍 焦点：ファンダメンタルズ（政治・経済・金利政策）を軸にし、テクニカル分析は不要です。

    ■ レポート構成
    【1】今週のマーケット総括🌍（「予想 〇〇 → 結果 〇〇」を基にした因果関係の詳述）
    【2】主要通貨の勢力図と背景（ドル・円・ユーロ。なぜその通貨が買われ/売られたか）
    【3】来週の注目材料と警戒シナリオ（{calendar_range} の重要イベントと市場予想）
    【4】来週の重要経済カレンダー（日付・曜日・重要度・市場予想値を正確に記載）
    """

    # 解析実行
    response = model.generate_content(prompt)
    report_text = response.text

    # LINE送信プロセス
    url = "https://api.me/v2/bot/message/push" # LINE API
    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    
    try:
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        print(f"送信エラー: {e}")

if __name__ == "__main__":
    main()
