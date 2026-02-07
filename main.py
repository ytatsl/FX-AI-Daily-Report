import os
import datetime
import yfinance as yf
import google.generativeai as genai
import requests
import pandas as pd

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Geminiの初期化
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def calculate_ma(df, window=20):
    """SMAとEMAを計算して最新値を返す"""
    sma = df['Close'].rolling(window=window).mean().iloc[-1]
    ema = df['Close'].ewm(span=window, adjust=False).mean().iloc[-1]
    return sma, ema

def get_technical_data(symbol):
    ticker = yf.Ticker(symbol)
    df_d = ticker.history(period="6mo", interval="1d")
    d_sma, d_ema = calculate_ma(df_d)
    d_close, d_high, d_low = df_d['Close'].iloc[-1], df_d['High'].iloc[-1], df_d['Low'].iloc[-1]
    df_4h = ticker.history(period="1mo", interval="4h")
    h4_sma, h4_ema = calculate_ma(df_4h)
    df_w = ticker.history(period="1y", interval="1wk")
    w_sma, w_ema = calculate_ma(df_w)
    return {
        "close": d_close, "high": d_high, "low": d_low,
        "d_sma": d_sma, "d_ema": d_ema,
        "h4_sma": h4_sma, "h4_ema": h4_ema,
        "w_sma": w_sma, "w_ema": w_ema
    }

def main():
    now = datetime.datetime.now()
    weekdays_ja = ['月', '火', '水', '木', '金', '土', '日']
    today_str = now.strftime('%Y年%m月%d日')
    weekday_str = weekdays_ja[now.weekday()]

    uj = get_technical_data("USDJPY=X")
    eu = get_technical_data("EURUSD=X")

    tech_data_text = f"""
    【USD/JPY リアルタイム数値】
    ・終値: {uj['close']:.2f} / 高値: {uj['high']:.2f} / 安値: {uj['low']:.2f}
    ・日足20MA: SMA {uj['d_sma']:.2f} / EMA {uj['d_ema']:.2f}
    ・4H足20MA: SMA {uj['h4_sma']:.2f} / EMA {uj['h4_ema']:.2f}
    ・週足20MA: SMA {uj['w_sma']:.2f} / EMA {uj['w_ema']:.2f}

    【EUR/USD リアルタイム数値】
    ・終値: {eu['close']:.4f} / 高値: {eu['high']:.4f} / 安値: {eu['low']:.4f}
    ・日足20MA: SMA {eu['d_sma']:.4f} / EMA {eu['d_ema']:.4f}
    ・4H足20MA: SMA {eu['h4_sma']:.4f} / EMA {eu['h4_ema']:.4f}
    ・週足20MA: SMA {eu['w_sma']:.4f} / EMA {eu['w_ema']:.4f}
    """

    prompt = f"""
    本日は {today_str}（{weekday_str}曜日）です。
    以下の数値に基づき、指定のスタイルでレポートを執筆してください。

    ■ 執筆スタイル・ルール（厳守）
    1. 構成: 「前日の振り返り」→「通貨別の詳細」→「本日の経済指標」
    2. デザイン: 
       - 見出しは「【1】本日のマーケット概況🌍」などの形式（### や () は禁止）。
       - セクション区切りは「━━━━━━━━━━━━」を使用。
       - 各段落や箇条書きには 💰、📈、⚠️、📊 などの絵文字を必ず1行ごとに使い、視認性を高めること。
    3. テクニカル: 4時間・日・週足の「20MA（SMA/EMA）」を軸に、フィボナッチや一目均衡表の視点も交え解説。
    4. 語り口: 冗長な挨拶は省き、プロ仕様の格調高い表現を維持。

    {tech_data_text}

    ■ 構成
    前日のドル円・ユーロドル相場振り返り
    ━━━━━━━━━━━━
    【1】ドル/円（USD/JPY）の前日動向
    ━━━━━━━━━━━━
    【2】ユーロ/ドル（EUR/USD）の前日動向
    ━━━━━━━━━━━━
    【3】本日の主な経済指標・イベント
    """

    response = model.generate_content(prompt)
    report_text = response.text

    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
