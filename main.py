import os
import yfinance as yf
import mplfinance as mpf
import google.generativeai as genai
import requests

# 1. 環境変数の読み込み（GitHub Secretsから取得）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 2. Geminiの初期化 (最新モデル: gemini-3-flash-preview)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def get_fx_data_and_charts(symbol):
    # チャート作成用のデータを取得
    # 週足(1年), 日足(3ヶ月), 4時間足(1ヶ月)
    data_w = yf.download(symbol, period='1y', interval='1wk')
    data_d = yf.download(symbol, period='3mo', interval='1d')
    data_4h = yf.download(symbol, period='1mo', interval='1h') # yfinanceは1hからリサンプリング

    # チャート画像を保存
    paths = []
    for tf, df in zip(['weekly', 'daily', '4h'], [data_w, data_d, data_4h]):
        path = f"{symbol}_{tf}.png"
        mpf.plot(df, type='candle', style='charles', savefig=path)
        paths.append(path)
    return paths

def main():
    pairs = ["USDJPY=X", "EURUSD=X"]
    full_report = "【FX Morning Report 6:30】\n"
    
    for pair in pairs:
        # 価格情報の取得（定量データ用）
        ticker = yf.Ticker(pair)
        current_price = ticker.history(period='1d')['Close'].iloc[-1]
        
        # ニュース・トレンド分析の指示
        prompt = f"""
        通貨ペア: {pair} (現在値: {current_price:.2f})
        
        以下の条件で、FX熟練者向けに1日の情報をまとめてください：
        1. トランプ関税政策や国内政局（衆院選・日銀）などの世界情勢トレンドを含め、大きな流れを解説。
        2. インジケーターは無視し、週足・日足・4時間足の「価格の動き（プライスアクション）」にのみ着目して現状を整理。
        3. 科学的根拠（統計的期待値や市場の織り込み度）に基づき、本日の注目ポイントを定量的に記述。
        """
        
        response = model.generate_content(prompt)
        full_report += f"\n--- {pair} ---\n{response.text}\n"

    # LINE送信
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": full_report}]
    }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
