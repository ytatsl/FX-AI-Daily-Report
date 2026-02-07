import os
import datetime
import yfinance as yf
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
    # 日付と曜日の取得
    now = datetime.datetime.now()
    weekdays_ja = ['月', '火', '水', '木', '金', '土', '日']
    today_str = now.strftime('%Y年%m月%d日')
    weekday_str = weekdays_ja[now.weekday()] # 自動で現在の曜日を取得
    
    # yfinanceから「嘘のつけない」実数値を取得
    try:
        # 直近2日分のデータを取得して前日比も出せるようにする
        uj = yf.Ticker("USDJPY=X").history(period='2d')
        eu = yf.Ticker("EURUSD=X").history(period='2d')
        
        uj_close = uj['Close'].iloc[-1]
        uj_high = uj['High'].iloc[-1]
        uj_low = uj['Low'].iloc[-1]
        uj_prev = uj['Close'].iloc[-2]
        uj_diff = uj_close - uj_prev
        
        eu_close = eu['Close'].iloc[-1]
        eu_high = eu['High'].iloc[-1]
        eu_low = eu['Low'].iloc[-1]
        eu_prev = eu['Close'].iloc[-2]
        eu_diff = eu_close - eu_prev
        
        market_stats = f"""
        【最新マーケット実数値】
        ・USD/JPY: 終値 {uj_close:.2f} (前日比 {uj_diff:+.2f}) / 高値 {uj_high:.2f} / 安値 {uj_low:.2f}
        ・EUR/USD: 終値 {eu_close:.4f} (前日比 {eu_diff:+.4f}) / 高値 {eu_high:.4f} / 安値 {eu_low:.4f}
        """
    except Exception as e:
        market_stats = "データ取得エラー。最新チャートを確認してください。"

    # AIへの指示：プロの時系列レポートを再現
    prompt = f"""
    本日は {today_str}（{weekday_str}曜日）です。
    為替アナリストとして、直近の「東京市場」「ロンドン市場」「ニューヨーク市場」の3市場の流れを総括してください。

    ■ 執筆ガイドライン（プロの流儀）
    1. 【時系列のバトンタッチ】「東京では〜」「ロンドンでは〜」「NYでは〜」という流れで、各市場での主要な材料（要人発言、経済指標、金利、地政学、商品市場のボラティリティ等）がどう連鎖したか記述すること。
    2. 【多角的な材料把握】特定のトピックだけでなく、日米欧の政局（選挙等）、中銀当局者の発言変化、実需の動き、テクニカル的な節目での攻防を網羅すること。
    3. 【不要な挨拶の排除】「市場が閉場した」等の冗長な説明は一切不要。冒頭から具体的な値動きとその背景から書き始めること。
    4. 【数字の絶対遵守】以下の実数値を使い、それと矛盾する解説（157円なのに156円と書く等）は厳禁。
    {market_stats}

    ■ 構成
    【1】本日のマーケット概況🌍（3市場の時系列・因果関係の詳述）
    【2】USD/JPY 分析🇯🇵🇺🇸（日米の政局・金利差・実需の視点）
    【3】EUR/USD 分析🇪🇺🇺🇸（欧州材料とドルの強弱）
    【4】今後の展望と注目イベント⏰（次週の重要指標や政治リスクへの備え）
    
    ※ 見出しに「###」や「()」は使用禁止。区切りは「━━━━━━━━━━━━」。
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
