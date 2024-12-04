from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import plotly.graph_objects as go
import datetime as dt

app = Flask(__name__)

# Function to fetch live prices for Nifty 50 and Bank Nifty
def fetch_nifty_data():
    indices = {"Nifty 50": "^NSEI", "Bank Nifty": "^NSEBANK"}
    live_prices = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)  # Establish session

        for name, symbol in indices.items():
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?region=IN&lang=en-IN"
            response = session.get(url, headers=headers)
            data = response.json()
            live_prices[name] = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except Exception as e:
        live_prices["error"] = str(e)
    return live_prices

# Function to generate sample historical data
def generate_historical_data(symbol):
    date_range = pd.date_range(end=dt.datetime.now(), periods=30)
    data = {
        "Date": date_range,
        "Open": [100 + i for i in range(30)],
        "High": [110 + i for i in range(30)],
        "Low": [90 + i for i in range(30)],
        "Close": [105 + i for i in range(30)],
    }
    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)

    # Calculate EMA and buy/sell signals
    df["9 EMA"] = df["Close"].ewm(span=9, adjust=False).mean()
    df["15 EMA"] = df["Close"].ewm(span=15, adjust=False).mean()
    df["Signal"] = None

    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["9 EMA"].iloc[i] and df["Close"].iloc[i - 1] <= df["9 EMA"].iloc[i - 1]:
            df.at[df.index[i], "Signal"] = "Buy"
        elif df["Close"].iloc[i] < df["15 EMA"].iloc[i] and df["Close"].iloc[i - 1] >= df["15 EMA"].iloc[i - 1]:
            df.at[df.index[i], "Signal"] = "Sell"

    return df

# Plot candlestick chart with buy/sell signals
def plot_chart(df, symbol):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="Candlestick"
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["9 EMA"], mode="lines", name="9 EMA", line=dict(color="blue")
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["15 EMA"], mode="lines", name="15 EMA", line=dict(color="red")
    ))

    buy_signals = df[df["Signal"] == "Buy"]
    sell_signals = df[df["Signal"] == "Sell"]

    fig.add_trace(go.Scatter(
        x=buy_signals.index, y=buy_signals["Close"], mode="markers", name="Buy",
        marker=dict(symbol="triangle-up", color="green", size=10)
    ))
    fig.add_trace(go.Scatter(
        x=sell_signals.index, y=sell_signals["Close"], mode="markers", name="Sell",
        marker=dict(symbol="triangle-down", color="red", size=10)
    ))

    fig.update_layout(
        title=f"{symbol} Candlestick Chart with Buy/Sell Signals",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark"
    )
    return fig.to_html(full_html=False)

@app.route("/", methods=["GET", "POST"])
def index():
    nifty_data = fetch_nifty_data()
    chart_div = None
    chart_symbol = None  # To pass the selected symbol for the TradingView widget
    if request.method == "POST":
        symbol = request.form["symbol"]
        chart_symbol = symbol.upper()  # Capitalize symbol for TradingView
        historical_data = generate_historical_data(symbol)
        chart_div = plot_chart(historical_data, symbol)
    return render_template("index.html", nifty_data=nifty_data, chart_div=chart_div, chart_symbol=chart_symbol)

@app.route("/get-live-prices")
def get_live_prices():
    return jsonify(fetch_nifty_data())

if __name__ == "__main__":
    app.run(debug=True)
