import requests
import openai
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from flask import Flask, jsonify, render_template_string, render_template, request
import yfinance as yf

app = Flask(__name__)

RAPIDAPI_HOST = "trend-and-strength-api-for-forex-gold-xauusd.p.rapidapi.com"
RAPIDAPI_KEY = "7269822340msh5c78026b319e7d1p1daca5jsn8daf44b56dbc"
OPENAI_API_KEY = "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"
ALPHA_VANTAGE_API_KEY = "5993OYS7TG4MFTVZ"
TWELVE_DATA_API_KEY = "e48e1ec5691e4018a17f445c1b4df45d"
MARKETSTACK_API_KEY = "ab8bb3169380914f49eac78b23eceace"
GOLDAPI_KEY = "goldapi-rrw1kmc9xftxz-io"
NINJA_API_KEY = "l/DM4jZ+8EODjH6vUX0mjw==1B0cHdtnazTFnGJ1"
METALPRICE_API_KEY = "a6e2126355ccf82074104572997fed1c"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/xauusd')
def get_xauusd():
    url = f"https://{RAPIDAPI_HOST}/XAUUSD"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers)
    return jsonify(response.json())

@app.route('/chart')
def chart():
    html = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>XAUUSD Live Chart</title>
    </head>
    <body>
        <h2>XAUUSD Live Chart (Gold/USD)</h2>
        <!-- TradingView Widget BEGIN -->
        <div class="tradingview-widget-container">
          <div id="tradingview_xauusd"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({
            "width": 980,
            "height": 610,
            "symbol": "OANDA:XAUUSD",
            "interval": "60",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_xauusd"
          });
          </script>
        </div>
        <!-- TradingView Widget END -->
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/news')
def gold_news():
    url = "https://forexnewsapi.com/api/v1"
    params = {
        "currencypair": "XAU-USD",
        "items": 3,
        "page": 1,
        "token": "sudnqb1v1umdmofcxrl65hoo9aenezqqawz0nx7a"
    }
    response = requests.get(url, params=params)
    return jsonify(response.json())

@app.route('/analyze', methods=['POST'])
def analyze():
    # Get price from frontend if provided
    price_from_user = None
    if request.is_json:
        price_from_user = request.json.get('price')

    # Fetch 1h interval, 2 days of price data from yfinance
    try:
        ticker = yf.Ticker('GC=F')
        data_hist = ticker.history(period='2d', interval='1h')
        if data_hist.empty:
            price_summary = 'No historical price data available.'
        else:
            closes = data_hist['Close'].tolist()
            highs = data_hist['High'].tolist()
            lows = data_hist['Low'].tolist()
            price_summary = (
                f"Last 1h closes (2 days): {closes}\n"
                f"Last 1h highs (2 days): {highs}\n"
                f"Last 1h lows (2 days): {lows}"
            )
    except Exception as e:
        price_summary = f"Failed to fetch historical price data: {e}"

    # Fetch latest XAUUSD data
    url = f"https://{RAPIDAPI_HOST}/XAUUSD"
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST,
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers)
    xauusd_data = response.json()

    # Fetch latest gold news
    news_url = "https://forexnewsapi.com/api/v1"
    news_params = {
        "currencypair": "XAU-USD",
        "items": 3,
        "page": 1,
        "token": "sudnqb1v1umdmofcxrl65hoo9aenezqqawz0nx7a"
    }
    news_response = requests.get(news_url, params=news_params)
    news_data = news_response.json().get('data', [])

    # Prepare prompt for ChatGPT
    prompt = f"""
You are a financial market analyst. Analyze the following XAUUSD (Gold/USD) market data, focusing on the 1-hour interval price action over the last 2 days, including the latest price, volume, and news headlines and sentiment. Provide a brief summary, including possible bullish or bearish signals, and any important technical or fundamental insights. Be concise and clear for a forex trader.

1h Interval Price Data (last 2 days):
{price_summary}

Market Data:
{xauusd_data}
"""
    if price_from_user:
        prompt += f"\nLatest Price (manual update): {price_from_user}\n"
    prompt += "\nLatest News:\n"
    for news in news_data:
        prompt += f"- {news.get('title', '')} (Sentiment: {news.get('sentiment', 'N/A')})\n"

    openai.api_key = OPENAI_API_KEY
    chat_response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    analysis = chat_response.choices[0].message.content.strip()
    return jsonify({"analysis": analysis})

@app.route('/price')
def price():
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": GOLDAPI_KEY}
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        price = data.get('price')
        volume = data.get('volume', 'N/A')
        if price is not None:
            return jsonify({"price": price, "volume": volume})
        else:
            return jsonify({"error": "No price in response", "raw": data})
    except Exception as e:
        return jsonify({"error": "Failed to fetch price/volume", "details": str(e), "raw": response.text})

@app.route('/signal', methods=['POST'])
def signal():
    # Get analysis and price from frontend if provided
    analysis_from_user = ''
    price_from_user = None
    if request.is_json:
        analysis_from_user = request.json.get('analysis', '')
        price_from_user = request.json.get('price')

    # Fetch 1h interval, 2 days of price data from yfinance
    try:
        ticker = yf.Ticker('GC=F')
        data_hist = ticker.history(period='2d', interval='1h')
        if data_hist.empty:
            price_summary = 'No historical price data available.'
        else:
            closes = data_hist['Close'].tolist()
            highs = data_hist['High'].tolist()
            lows = data_hist['Low'].tolist()
            price_summary = (
                f"Last 1h closes (2 days): {closes}\n"
                f"Last 1h highs (2 days): {highs}\n"
                f"Last 1h lows (2 days): {lows}"
            )
    except Exception as e:
        price_summary = f"Failed to fetch historical price data: {e}"

    # Fetch live price and volume from GoldAPI
    url = "https://www.goldapi.io/api/XAU/USD"
    headers = {"x-access-token": GOLDAPI_KEY}
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        price = data.get('price')
        volume = data.get('volume', 'N/A')
        if price_from_user:
            price = price_from_user
        if price is None:
            return jsonify({"signal": "No price from GoldAPI or frontend."})
    except Exception as e:
        return jsonify({"signal": f"Failed to fetch price/volume: {e}"})

    # Calculate indicators using yfinance as fallback (for historical data)
    try:
        ticker = yf.Ticker('GC=F')
        data_hist_ind = ticker.history(period='7d', interval='1m')
        if data_hist_ind.empty:
            rsi = macd = macd_signal = 'N/A'
        else:
            rsi = RSIIndicator(close=data_hist_ind['Close'], window=14).rsi().iloc[-1]
            macd_obj = MACD(close=data_hist_ind['Close'])
            macd = macd_obj.macd().iloc[-1]
            macd_signal = macd_obj.macd_signal().iloc[-1]
    except Exception:
        rsi = macd = macd_signal = 'N/A'

    # Fetch latest gold news
    news_url = "https://forexnewsapi.com/api/v1"
    news_params = {
        "currencypair": "XAU-USD",
        "items": 3,
        "page": 1,
        "token": "sudnqb1v1umdmofcxrl65hoo9aenezqqawz0nx7a"
    }
    news_response = requests.get(news_url, params=news_params)
    news_data = news_response.json().get('data', [])

    # Prepare prompt for ChatGPT
    prompt = f"""
You are a professional forex trading assistant. Based on the following live gold price (XAU/USD), volume, technical indicators (RSI, MACD), the latest news headlines and sentiment, and the following analysis, generate a trading signal for the next 1-4 hours.

1h Interval Price Data (last 2 days):
{price_summary}

Analysis:
{analysis_from_user}

Please provide your answer in the following format, and ensure that the Take Profit (TP) and Stop Loss (SL) are set with a risk-reward ratio of 1:1.5:

Details and Explain why:
Buy/Sell:
Entry Price:
TP:
SL:

Latest Market Data (1m):
Price: {price}
Volume: {volume}
RSI: {rsi}
MACD: {macd}
MACD Signal: {macd_signal}

Latest News:
"""
    for news in news_data:
        prompt += f"- {news.get('title', '')} (Sentiment: {news.get('sentiment', 'N/A')})\n"

    openai.api_key = OPENAI_API_KEY
    chat_response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    signal = chat_response.choices[0].message.content.strip()
    return jsonify({"signal": signal})

@app.route('/price_ninja')
def price_ninja():
    url = "https://world-gold-price-live-api.p.rapidapi.com/api/World-Gold-Rates/?country=us"
    headers = {
        "x-rapidapi-host": "world-gold-price-live-api.p.rapidapi.com",
        "x-rapidapi-key": RAPIDAPI_KEY
    }
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
        price = data.get('gold_price')
        if price is not None:
            return jsonify({"price": price})
        else:
            return jsonify({"error": "No gold_price in response", "raw": data})
    except Exception as e:
        return jsonify({"error": "Failed to fetch price", "details": str(e), "raw": response.text})

if __name__ == '__main__':
    app.run(debug=True) 