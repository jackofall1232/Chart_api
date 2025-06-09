from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import io
import os

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    data = request.json

    df = pd.DataFrame(data["ohlc"])
    df.index = pd.to_datetime(df["timestamp"])
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # MACD Calculation
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - signal

    style = mpf.make_mpf_style(base_mpf_style='nightclouds')
    mc = mpf.make_marketcolors(up='green', down='red', inherit=True)

    fig = plt.figure(figsize=(10, 8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1])

    # Candlestick Chart
    ax1 = fig.add_subplot(gs[0])
    mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        ax=ax1,
        style=mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc),
        volume=False,
        show_nontrading=False
    )
    ax1.set_title(f"{data.get('pair', 'Crypto Chart')} – {data.get('timeframe', '')} Chart", fontsize=14, weight='bold')
    ax1.set_ylabel('Price')

    # Add watermark
    logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
    if os.path.exists(logo_path):
        try:
            img = plt.imread(logo_path)
            x_min, x_max = ax1.get_xlim()
            y_min, y_max = ax1.get_ylim()
            ax1.imshow(
                img,
                extent=(x_min, x_max, y_min, y_max),
                alpha=0.1,
                aspect='auto',
                zorder=-1
            )
        except Exception as e:
            print(f"Error adding watermark: {e}")
    else:
        print(f"Logo file not found at: {logo_path}")

    # MACD Subplot
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.plot(df.index, macd, label='MACD', color='cyan')
    ax2.plot(df.index, signal, label='Signal', color='magenta')
    ax2.bar(df.index, hist, label='Histogram',
            color=['green' if val >= 0 else 'red' for val in hist], width=0.01)
    ax2.axhline(0, color='white', linewidth=0.5)
    ax2.legend(loc='upper left')
    ax2.set_title("MACD", fontsize=10)

    # Output to buffer
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=False)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
