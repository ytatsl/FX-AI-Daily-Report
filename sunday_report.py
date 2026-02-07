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
    # 日付の計算（自動化のキモ）
    now = datetime.datetime.now()
    today_str = now.strftime('%Y年%m月%d日')
    
    # 「来週（明日月曜日から来週日曜日まで）」の期間を計算
    next_monday = (now + datetime.timedelta(days=1)).strftime('%m月%d日')
    next_sunday = (now + datetime.timedelta(days=7)).strftime('%m月%d日')
    calendar_period = f"{next_monday}〜{next_sunday}"

    # AIへの指示（日付計算をAIに任せず、プログラムが教える）
    prompt = f"""
    【最優先：日付の整合性】
    本日は {today_str}（日曜日）です。
    分析対象となる「来週」とは、明日からの【{calendar_period}】の期間を指します。
    
    ■ 厳守事項
    1. 2026年のカレンダーに基づき、{calendar_period} 内に行われる経済指標の「正しい日付と曜日」を検索して確定させてください。
    2. CPI、雇用統計、中銀政策決定会合など、主要指標の日付ミスは専門家として致命的です。必ず複数のニュースソースから照合してください。
    3. 「来週の展望」としながら、先週や先々週の古い予定を記載することは絶対に避けてください。

    ■ 執筆ルール
    💰 1週間の総括：先週の材料（政局、中銀発言、コモディティ等）の因果関係。
    📈 来週の展望：ファンダメンタルズ重視（政治・経済・金利政策）で、テクニカルは補足程度。
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
