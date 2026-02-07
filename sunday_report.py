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
    now = datetime.datetime.now()
    today_str = now.strftime('%Y年%m月%d日')

    # AIへの指示（日付の正確性を極限まで高める）
    prompt = f"""
    【最重要指示：日付の正確性】
    本日は {today_str}（日曜日）です。
    来週（2月9日〜2月15日の週）の展望をまとめますが、経済指標の日付を絶対に間違えないでください。
    
    ■ 検索・確認の徹底
    1. 2026年2月のカレンダーを正確に把握してください（例：2/13は金曜日です）。
    2. 米CPI（消費者物価指数）など、重要指標の「正確な発表日」を最新の検索結果から照合してください。
    3. もし正確な日付に自信がない場合は「来週中盤」などのぼかした表現にするか、必ず「〇月〇日(曜日)」まで明記して再確認してください。

    ■ 執筆ルール
    💰 1週間の総括：先週の材料（政局、中銀発言、コモディティ等）がどう結びついたか。
    📈 来週の展望：ファンダメンタルズ（政治・経済情勢）に特化し、テクニカルは控えめに。
    ⚠️ 視認性：1行ごとに絵文字（💰、📈、⚠️、🌍等）を使用。
    📊 フォーマット：見出し「【1】見出し🌍」、区切り「━━━━━━━━━━━━」。

    ■ 構成
    【1】今週のマーケット総括🌍（材料間の因果関係を深掘り）
    【2】主要通貨の勢力図と背景（ドル・円・ユーロの強弱理由）
    【3】来週の注目材料と警戒シナリオ（日付を厳密に確認した上での展望）
    【4】来週の重要経済カレンダー（日付と曜日が一致しているか最終確認すること）
    """

    response = model.generate_content(prompt)
    report_text = response.text

    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
