import os
import datetime
import yfinance as yf
import google.generativeai as genai
import requests

# 1. 環境変数の読み込み
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Geminiの初期化 (gemini-3-flash-preview)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def main():
    # 日付設定
    now = datetime.datetime.now()
    today_str = now.strftime('%Y年%m月%d日')
    
    # 実際の「本物のデータ」を詳細に取得
    try:
        # USD/JPYのデータを取得
        uj = yf.Ticker("USDJPY=X").history(period='2d') # 2日分取って比較
        uj_close = uj['Close'].iloc[-1]
        uj_high = uj['High'].iloc[-1]
        uj_low = uj['Low'].iloc[-1]
        uj_change = uj_close - uj['Close'].iloc[-2]
        
        # EUR/USDのデータを取得
        eu = yf.Ticker("EURUSD=X").history(period='2d')
        eu_close = eu['Close'].iloc[-1]
        eu_high = eu['High'].iloc[-1]
        eu_low = eu['Low'].iloc[-1]
        eu_change = eu_close - eu['Close'].iloc[-2]
        
        market_data = f"""
        【最新マーケット数値（嘘厳禁）】
        ・ドル円(USD/JPY): 終値{uj_close:.2f} / 高値{uj_high:.2f} / 安値{uj_low:.2f} / 前日比{uj_change:+.2f}
        ・ユーロドル(EUR/USD): 終値{eu_close:.4f} / 高値{eu_high:.4f} / 安値{eu_low:.4f} / 前日比{eu_change:+.4f}
        """
    except:
        market_data = "データ取得エラー。最新チャートを確認してください。"

    # AIへの指示（データ至上主義に変更）
    prompt = f"""
    本日は {today_str} です。あなたはデータ至上主義のFXアナリストです。
    以下の【最新マーケット数値】を「絶対的な事実」として使い、嘘を一切つかずにレポートを書いてください。
    
    {market_data}

    ■ 必須ルール
    1. 【情報源】自分の記憶にある古いレート（149円や1.17など）はゴミ箱に捨ててください。上記の数値のみを使用すること。
    2. 【時間軸】今は週末（土曜朝）です。昨日（金曜）の東京・欧州・ニューヨーク市場が全て閉まった直後の総括をしてください。
    3. 【ファンダメンタルズ】現在の世界情勢（トランプ政権の動向、日米欧の金利差、最新の経済指標）が、上記の「数値（上昇・下落）」にどう結びついたか、論理的に推測して書いてください。
    4. 【禁止事項】### や () の使用は禁止。見出しは「【1】見出し🌍」の形式にすること。

    ■ 構成
    【1】本日のマーケット概況🌍（3市場の総括）
    【2】USD/JPY 分析🇯🇵🇺🇸（上記の高値・安値を踏まえた解説）
    【3】EUR/USD 分析🇪🇺🇺🇸（上記の終値を踏まえたドルの強弱解説）
    【4】今後の注目イベント⏰（週明けの展望）
    """

    response = model.generate_content(prompt)
    report_text = response.text

    # LINE送信
    url = "https://api.line.me/v2/bot/message/push"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    payload = {"to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}]}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
