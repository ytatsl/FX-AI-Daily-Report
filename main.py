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
    today = datetime.date.today().strftime('%Y年%m月%d日')
    
    # 通貨ペア（ yfinance用）
    pairs = ["USDJPY=X", "EURUSD=X"]
    
    # AIへの指示（最新ルール・デザイン・日付情報を反映）
    prompt = f"""
    【重要】本日は {today} です。
    
    あなたはプロのFXストラテジスト兼、人気LINEマガジンの編集者です。
    USD/JPYとEUR/USDについて、投資家に届ける「朝刊レポート」を作成してください。
    
    ■ 配信ルール（厳守）
    1. 【冒頭】文章の最初には必ず「{today} のFX朝刊レポート」というタイトルを入れて始めてください。
    2. 【情報鮮度】直近24時間の最新材料に絞って伝えること。ただし、文脈の関係から今週先週や今月先月などの情報を書いた方が伝わりやすいと判断した場合は追加で書いても良い。2025年の古い情報は文脈上必要がない限り除外すること。
    3. 【視認性】スマホで読みやすいよう、以下の装飾を多用すること。
       - セクションの区切りには「━━━━━━━━━━━━」を使用。
       - 見出しには ▷▷ や 【 】 を使う。
       - 箇条書きには 💰、📈、⚠️ などの絵文字を1行ごとに使う。
       - 適宜、空白行を入れて文章が詰まりすぎないようにする。
    4. 【分析】価格の動き（プライスアクション）に集中し、具体的な節目価格（何円、何ドル）を定量的に出すこと。

    ■ 構成
    【1】本日のマーケット概況（🌍）
    【2】USD/JPY 分析（🇯🇵🇺🇸）
    【3】EUR/USD 分析（🇪🇺🇺🇸）
    【4】本日の注目イベント（⏰）
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
