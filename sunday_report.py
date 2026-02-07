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
    current_year = now.year
    today_str = now.strftime('%Y年%m月%d日')
    
    # 来週の期間を計算
    next_monday_dt = now + datetime.timedelta(days=1)
    next_sunday_dt = now + datetime.timedelta(days=7)
    
    next_monday_str = next_monday_dt.strftime('%m月%d日')
    next_sunday_str = next_sunday_dt.strftime('%m月%d日')
    calendar_period = f"{next_monday_str}〜{next_sunday_str}"

    # AIへの指示（定量的な比較とサプライズの記述を指示）
    prompt = f"""
    【最優先：定量的分析と日付の整合性】
    本日は {today_str}（日曜日）です。
    {current_year}年の【{calendar_period}】の展望を含む「週刊為替ファンダメンタルズ・レポート」を執筆してください。
    
    ■ 執筆ルール（重要）
    1. 【定量的な比較】主要な経済指標の結果に触れる際は、必ず「予想 〇〇 → 結果 〇〇」という形式で記述し、その乖離が市場に「ポジティブ・サプライズ」だったのか「予想通り」だったのかを明記してください。
    2. 【日付の厳守】{current_year}年のカレンダーに基づき、{calendar_period} の予定を最新ソースと照合してください。
    3. 【視認性】1行ごとに絵文字（💰、📈、⚠️、📊等）を使用し、見出しは「【1】見出し🌍」、区切りは「━━━━━━━━━━━━」を徹底してください。

    ■ 構成
    【1】今週のマーケット総括🌍
    （主要指標の「予想 vs 結果」を交え、なぜその値動きになったかの因果関係を深掘り）
    【2】主要通貨の勢力図と背景
    （ドル・円・ユーロの強弱をファンダメンタルズ視点で整理）
    【3】来週の注目材料と警戒シナリオ
    （{calendar_period} の重要イベントと、市場の予想コンセンサス）
    【4】来週の重要経済カレンダー
    （日付、曜日、重要度、予想値を指差し確認して記載）
    """

    response = model.generate_content(prompt)
    report_text = response.text

    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
