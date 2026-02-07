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

# 2. Geminiの初期化 (最新版指定)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

def calculate_ma(df, window=20):
    """SMAとEMAを計算して最新値を返す"""
    sma = df['Close'].rolling(window=window).mean().iloc[-1]
    ema = df['Close'].ewm(span=window, adjust=False).mean().iloc[-1]
    return sma, ema

def get_technical_data(symbol):
    ticker = yf.Ticker(symbol)
    
    # 日足データ (20MA計算用)
    df_d = ticker.history(period="6mo", interval="1d")
    d_sma, d_ema = calculate_ma(df_d)
    d_close = df_d['Close'].iloc[-1]
    d_high = df_d['High'].iloc[-1]
    d_low = df_d['Low'].iloc[-1]
    
    # 4時間足データ
    df_4h = ticker.history(period="1mo", interval="4h")
    h4_sma, h4_ema = calculate_ma(df_4h)
    
    # 週足データ
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

    # テクニカル指標の取得
    uj = get_technical_data("USDJPY=X")
    eu = get_technical_data("EURUSD=X")

    # データをAIに渡す用のテキスト
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

    # AIへの指示（提供された理想の文章を再現）
    prompt = f"""
    本日は {today_str}（{weekday_str}曜日）です。
    以下の【リアルタイム数値】に基づき、プロの為替アナリストとして最高品質の朝刊レポートを執筆してください。

    ■ 執筆スタイル（徹底再現）
    1. 構成: 「前日の振り返り」→「通貨別の詳細（前日動向）」→「本日の経済指標・イベント」の流れ。
    2. テクニカル分析: 提供した「4時間足・日足・週足の20MA(SMA/EMA)」を必ず引用し、現在値との乖離やサポート・レジスタンスとしての機能性を論理的に解説すること。
    3. プロの視点: フィボナッチ（数値からの推測）、一目均衡表、当局の介入警戒、政局（衆院選等）、実需の動きを適宜織り交ぜること。
    4. 語り口: 冗長な挨拶は省き、格調高く、かつ scannable（読みやすい）な形式。

    {tech_data_text}

    ■ 構成案
    前日のドル円・ユーロドル相場振り返り
    （東京→ロンドン→NYの流れと、ファンダメンタルズの相関）
    ━━━━━━━━━━━━
    ドル/円（USD/JPY）の前日動向
    （数値に基づき、20MAとの位置関係や重要水準、当局の警戒感を詳述）
    ━━━━━━━━━━━━
    ユーロ/ドル（EUR/USD）の前日動向
    （欧州情勢とドルの強弱、テクニカル面での戻り売り圧力を解説）
    ━━━━━━━━━━━━
    本日の主な経済指標・イベント
    （発表予定とその予想値、市場への影響度を定量的に記述）
    """

    # 解析実行
    response = model.generate_content(prompt)
    report_text = response.text

    # LINE送信
    url = "https://api.line.me/v2/bot/message/push"
    headers = { "Content-Type": "application/json", "Authorization": f"Bearer {LINE_ACCESS_TOKEN}" }
    payload = { "to": LINE_USER_ID, "messages": [{"type": "text", "text": report_text}] }
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    main()
