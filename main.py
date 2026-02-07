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
    # 実行日の日付を取得
    now = datetime.datetime.now()
    today_str = now.strftime('%Y年%m月%d日')
    
    # 実際の現在レートを取得
    try:
        usdjpy_rate = round(yf.Ticker("USDJPY=X").history(period='1d')['Close'].iloc[-1], 2)
        eurusd_rate = round(yf.Ticker("EURUSD=X").history(period='1d')['Close'].iloc[-1], 4)
    except Exception as e:
        usdjpy_rate = "157.20前後(取得エラー)"
        eurusd_rate = "1.0800前後(取得エラー)"
    
    # AIへの指示（3大市場の網羅とファンダメンタルズ深掘り）
    prompt = f"""
    【重要】本日は {today_str} です。
    FX熟練者向けの「朝刊マガジン」を作成してください。
    
    ■ 分析のポイント（厳守）
    1. 【3大市場の推移】直近24時間の「東京・ロンドン・ニューヨーク」各市場の主要な動きを時系列で整理し、それぞれの市場がどう為替に影響を与えたか分析してください。
    2. 【世界情勢・ファンダメンタルズ】
       - トランプ政権の経済政策、日銀・FRB・ECBの金融政策の方向性、地政学リスクなど、大局的な流れを詳しく記述すること。
       - それらの材料が、直近のプライスアクションにどう繋がっているかの因果関係を明確にすること。
    3. 【鮮度】実行時点から遡って24時間の情報を最優先。古いニュース（数日前など）は、今のトレンドを説明するための背景としてのみ使用すること。

    ■ 配信ルール
    1. 【冒頭】必ず「{today_str} のFX朝刊レポート」というタイトルから始めてください。
    2. 【視認性】ご指定のフォーマットを徹底。
       - 見出しに「###」や「()」は絶対に使用禁止。
       - セクションの区切りには「━━━━━━━━━━━━」を使用。
       - 見出し例：【1】本日のマーケット概況🌍
       - 箇条書きには 💰、📈、⚠️ などの絵文字を1行ごとに使う。
    3. 【定量分析】今のレート（USD/JPY:{usdjpy_rate} / EUR/USD:{eurusd_rate}）に基づいた具体的な節目価格を提示すること。

    ■ 構成
    【1】本日のマーケット概況🌍（東京・欧州・米国の流れ）
    【2】USD/JPY 分析🇯🇵🇺🇸（世界情勢と連動した分析）
    【3】EUR/USD 分析🇪🇺🇺🇸（欧州経済とドルの強弱）
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
