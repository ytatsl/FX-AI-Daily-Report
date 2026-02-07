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
    # 日付の計算（AIの混乱を防ぐ）
    now = datetime.datetime.now()
    today_str = now.strftime('%Y年%m月%d日')
    yesterday_str = (now - datetime.timedelta(days=1)).strftime('%Y年%m月%d日')
    tomorrow_str = (now + datetime.timedelta(days=1)).strftime('%Y年%m月%d日')
    
    # 実際のリアルタイムレートを取得
    try:
        # 直近の終値を取得
        usdjpy_ticker = yf.Ticker("USDJPY=X")
        eurusd_ticker = yf.Ticker("EURUSD=X")
        usdjpy_rate = round(usdjpy_ticker.history(period='1d')['Close'].iloc[-1], 2)
        eurusd_rate = round(eurusd_ticker.history(period='1d')['Close'].iloc[-1], 4)
    except Exception as e:
        usdjpy_rate = "157.20前後(取得エラー)"
        eurusd_rate = "1.0800前後(取得エラー)"
    
    # AIへの指示（時間軸のズレを物理的に修正）
    prompt = f"""
    【重要：時間軸の設定】
    本日は {today_str}（土曜）の朝です。
    ・「昨晩」とは、{yesterday_str}（金曜）のニューヨーク市場のことです。
    ・「昨日」とは、{yesterday_str}（金曜）の東京・欧州市場のことです。
    
    あなたは今、{yesterday_str}の全市場が閉まった直後の最新データを分析しています。
    この前提に基づき、FX熟練者向けの朝刊レポートを作成してください。

    ■ 分析のポイント
    1. 【3大市場の完結】{yesterday_str}の東京・ロンドン・ニューヨーク市場の一連の流れを総括すること。特に昨晩のNY終値時点での大局を書いてください。
    2. 【ファンダメンタルズ】世界情勢（トランプ政権、金利差、地政学）がどう相場を支配したか深掘りすること。
    3. 【情報の整合性】現在のレート（USD/JPY:{usdjpy_rate} / EUR/USD:{eurusd_rate}）と矛盾する、1日前の古い価格データは絶対に使わないこと。

    ■ 配信ルール
    1. 【冒頭】必ず「{today_str} のFX朝刊レポート」というタイトルから始めてください。
    2. 【視認性】ご指定のフォーマットを徹底。
       - 見出しに「###」や「()」は絶対に使用禁止。
       - セクションの区切りには「━━━━━━━━━━━━」を使用。
       - 見出し例：【1】本日のマーケット概況🌍
       - 箇条書きには 💰、📈、⚠️ などの絵文字を1行ごとに使う。
    3. 【土日の扱い】本日は土曜で市場が閉まるため、週明けの展望や、週末の注目材料に触れてください。

    ■ 構成
    【1】本日のマーケット概況🌍（昨日から今朝にかけての全市場の流れ）
    【2】USD/JPY 分析🇯🇵🇺🇸（ファンダメンタルズ重視）
    【3】EUR/USD 分析🇪🇺🇺🇸（欧州とドルの強弱関係）
    【4】今後の注目イベント⏰（週明けの予定など）
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
