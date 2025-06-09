from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import io
import os

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    data = request.json

    # Create DataFrame
    df = pd.DataFrame(data["ohlc"])
    df.index = pd.to_datetime(df["timestamp"])
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Set dark theme with custom red/green candles
    mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
    style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

    # Plot chart
    fig, axlist = mpf.plot(
        df,
        type='candle',
        style=style,
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        returnfig=True,
        figsize=(8, 6),
        title="Crypto Chart"
    )

    # Add faint watermark logo if available
    logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
    if os.path.exists(logo_path):
        img = plt.imread(logo_path)
        ax = axlist[0]
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        ax.imshow(img, aspect='auto', extent=(x_min, x_max, y_min, y_max), alpha=0.08, zorder=0)

    # Output to memory
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)

    return send_file(buf, mimetype='image/png')
