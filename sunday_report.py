import os
import datetime
import google.generativeai as genai
import requests

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Geminiの初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def main():
    # 実行時の「年・月・日」をすべて自動取得
    now = datetime.datetime.now()
    current_year = now.year
    today_str = now.strftime('%Y年%m月%d日')
    
    # 来週の期間を計算（月曜〜日曜）
    next_monday_dt = now + datetime.timedelta(days=1)
    next_sunday_dt = now + datetime.timedelta(days=7)
    
    next_monday_str = next_monday_dt.strftime('%m月%d日')
    next_sunday_str = next_sunday_dt.strftime('%m月%d日')
    calendar_period = f"{next_monday_str}〜{next_sunday_str}"

    # AIへの指示：嘘の捏造を「規約違反」として厳禁するプロンプト
    prompt = f"""
    【最重要：情報の真実性と定量的な正確性】
    本日は {today_str}（日曜日）です。
    {current_year}年の【{calendar_period}】の展望を含む週刊ファンダメンタルズ・レポートを執筆してください。
    
    ■ 嘘・捏造に関する絶対禁止ルール（厳守）
    1. 経済指標の「結果」について、検索しても確定値が見当たらない場合（延期、未発表、未実施）は、絶対に数値を捏造しないでください。
    2. 先週、雇用統計などの重要指標が「発表延期」になった事実があるなら、それをそのまま記述してください。「あったはず」という推測で架空の数値を書くことは重大な誤りです。
    3. 数値の出所が不明な場合は「発表なし」または「データなし」と明記すること。

    ■ 執筆ルール
    💰 1週間の総括：主要指標の「予想 vs 結果」を対比し、乖離（サプライズ）が市場に与えた影響を定量的に分析してください。
    📈 来週の展望：{current_year}年の【{calendar_period}】に行われる予定を最新ソースで照合し、ファンダメンタルズ視点で詳述。
    ⚠️ 視認性：1行ごとに絵文字（💰、📈、⚠️、📊等）を必ず使用。
    📊 構成：見出し「【1】見出し🌍」、区切り「━━━━━━━━━━━━」を徹底。

    ■ 構成案
    【1】今週のマーケット総括🌍（「予想 〇〇 → 結果 〇〇」を明記。延期時はその旨を記述）
    【2】主要通貨の勢力図と背景（ドル・円・ユーロの強弱因果関係）
    【3】来週の注目材料と警戒シナリオ（{calendar_period} の重要イベント）
    【4】来週の重要経済カレンダー（日付・曜日・予想値を最新ソースから指差し確認）
    """

    # AI解析実行
    response = model.generate_content(prompt)
    report_text = response.text

    # LINE送信
    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
