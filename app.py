from flask import Flask, request, send_file
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import pandas as pd
import mplfinance as mpf
import numpy as np
import io
import os

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    # Get JSON data from request
    data = request.json

    # Create DataFrame from OHLC data
    df = pd.DataFrame(data["ohlc"])
    df.index = pd.to_datetime(df["timestamp"])
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Calculate MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    # Define chart style
    mc = mpf.make_marketcolors(up='green', down='red')
    s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

    # Create figure with GridSpec
    fig = plt.figure(figsize=(10, 8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

    # Main candlestick chart
    ax1 = fig.add_subplot(gs[0])
    mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),
        ax=ax1,
        hlines=dict(hlines=data.get("support", []), colors='red'),
        style=s,
        volume=False,
        show_nontrading=False
    )
    ax1.set_title(f"{data.get('pair', 'Crypto Chart')} – {data.get('timeframe', '')} Chart", fontsize=14, weight='bold')

    # MACD chart
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(df.index, macd, label='MACD', color='cyan')
    ax2.plot(df.index, signal, label='Signal', color='magenta')
    ax2.bar(df.index, hist, label='Histogram',
            color=['green' if val >= 0 else 'red' for val in hist], width=0.01)
    ax2.axhline(0, color='white', linewidth=0.5)
    ax2.legend(loc='upper left')
    ax2.set_title("MACD", fontsize=10)

    # Adjust layout and save to buffer
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
