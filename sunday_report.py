import os
import datetime
import google.generativeai as genai
import requests

# 環境変数
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def main():
    # 実行時の「年・月・日」をすべて自動取得
    now = datetime.datetime.now()
    current_year = now.year  # 2026, 2027...と自動で変わる
    today_str = now.strftime('%Y年%m月%d日')
    
    # 来週の期間を計算
    next_monday_dt = now + datetime.timedelta(days=1)
    next_sunday_dt = now + datetime.timedelta(days=7)
    
    # AIに渡すための期間テキスト
    next_monday_str = next_monday_dt.strftime('%m月%d日')
    next_sunday_str = next_sunday_dt.strftime('%m月%d日')
    calendar_period = f"{next_monday_str}〜{next_sunday_str}"

    # AIへの指示（年・月・日をすべて変数で渡す）
    prompt = f"""
    【最優先：日付の整合性】
    本日は {today_str}（日曜日）です。
    分析対象となる「来週」とは、{current_year}年の【{calendar_period}】の期間を指します。
    
    ■ 厳守事項
    1. {current_year}年のカレンダーに基づき、{calendar_period} 内に行われる経済指標の「正しい日付と曜日」を検索して確定させてください。
    2. CPI、雇用統計、中銀政策決定会合など、主要指標の日付ミスは専門家として致命的です。必ず最新のソースと照合してください。
    3. 「来週の展望」において、過去の年度や古い月の情報を混ぜることは絶対に避けてください。

    ■ 執筆ルール
    💰 1週間の総括：先週の材料（政局、中銀発言、商品市場等）の因果関係を整理。
    📈 来週の展望：ファンダメンタルズ（政治・経済・金利政策）に特化。
    ⚠️ 視認性：1行ごとに絵文字（💰、📈、⚠️、🌍等）を使用。
    📊 フォーマット：見出し「【1】見出し🌍」、区切り「━━━━━━━━━━━━」。

    ■ 構成
    【1】今週のマーケット総括🌍
    【2】主要通貨の勢力図と背景（ドル・円・ユーロ）
    【3】来週の注目材料と警戒シナリオ（{calendar_period} の展望）
    【4】来週の重要経済カレンダー（日付と曜日を指差し確認すること）
    """

    response = model.generate_content(prompt)
    report_text = response.text

    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
