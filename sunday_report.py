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

    prompt = f"""
    本日は {today_str} 日曜日です。今週1週間の市場動向を振り返り、来週の展望をまとめた「週刊為替ファンダメンタルズ・レポート」を執筆してください。

    ■ 執筆ルール
    1. 【ファンダメンタルズ重視】テクニカル分析は控えめにし、各国の政策金利、経済指標の結果、政局（衆院選やトランプ政権の動向等）、地政学リスク、コモディティ価格の変動が「どう市場のテーマを変えたか」を重点的に解説してください。
    2. 【1週間の総括】月曜から金曜にかけての主要な流れをダイジェストでまとめ、現在市場が何を最も意識して週末を迎えているかを整理してください。
    3. 【来週の展望】週明けの月曜日以降、どのイベントや発言がトリガーとなって相場が動くか、複数のシナリオを提示してください。
    4. 【視認性】1行ごとに絵文字（💰、📈、⚠️、🌍等）を使い、見出しは「【1】見出し🌍」、区切りは「━━━━━━━━━━━━」を徹底してください。

    ■ 構成
    【1】今週のマーケット総括🌍（主要ニュースの因果関係）
    【2】主要通貨の勢力図と背景（ドル・円・ユーロの力関係）
    【3】来週の注目材料と警戒シナリオ（政局や経済イベント）
    【4】来週の重要経済カレンダー
    """

    response = model.generate_content(prompt)
    report_text = response.text

    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
