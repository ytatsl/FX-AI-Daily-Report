import os
import datetime
import yfinance as yf
import google.generativeai as genai
import requests

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Geminiの初期化 (最新モデル: gemini-3-flash-preview)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def main():
    # 実行日の日付を自動取得
    now = datetime.datetime.now()
    today_str = now.strftime('%Y年%m月%d日')
    
    # 2日前の日付を自動計算（古い情報を排除する基準日）
    two_days_ago = (now - datetime.timedelta(days=2)).strftime('%Y年%m月%d日')
    
    # 実際の現在レートを取得（AIに嘘をつかせないための「真実」のデータ）
    try:
        # yfinanceから最新終値を取得
        usdjpy_rate = round(yf.Ticker("USDJPY=X").history(period='1d')['Close'].iloc[-1], 2)
        eurusd_rate = round(yf.Ticker("EURUSD=X").history(period='1d')['Close'].iloc[-1], 4)
    except Exception as e:
        usdjpy_rate = "157.20前後(取得エラー)"
        eurusd_rate = "1.0800前後(取得エラー)"
    
    # AIへの指示（日付・レート・フォーマットの厳格化）
    prompt = f"""
    【重要】本日は {today_str} です。
    必ず最新の検索結果と、以下のリアルタイムレートを使用して正確なレポートを作成してください。
    ・現在のドル円レートは約 {usdjpy_rate} 円
    ・ユーロドルレートは約 {eurusd_rate} ドル
    これと矛盾する過去の数値は絶対に書かないでください。
    
    ■ 配信ルール（厳守）
    1. 【冒頭】文章の最初には必ず「{today_str} のFX朝刊レポート」というタイトルを入れて始めてください。
    2. 【情報鮮度】{two_days_ago} より前の古いニュースを「昨晩のメイン材料」として扱うのは厳禁です。直近24時間の材料を最優先してください。ただし、文脈の関係から今週先週や今月先月などの情報を書いた方が伝わりやすいと判断した場合は追加で書いても良い。
    3. 【視認性】ご指定のフォーマットを徹底してください。
       - 見出しに「###」や「()」は絶対に使用禁止。
       - セクションの区切りには「━━━━━━━━━━━━」を使用。
       - 見出し例：【1】本日のマーケット概況🌍
       - 箇条書きには 💰、📈、⚠️ などの絵文字を1行ごとに使う。
    4. 【分析】価格の動き（プライスアクション）に集中し、具体的な節目価格（今のレート {usdjpy_rate} / {eurusd_rate} に基づいた数値）を出すこと。

    ■ 構成
    【1】本日のマーケット概況🌍
    【2】USD/JPY 分析🇯🇵🇺🇸
    【3】EUR/USD 分析🇪🇺🇺🇸
    【4】本日の注目イベント⏰
    """

    # AI解析実行
    response = model.generate_content(prompt)
    report_text = response.text

    # LINE送信
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": report_text}]
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
