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

    df = pd.DataFrame(data["ohlc"])
    df.index = pd.to_datetime(df["timestamp"])
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Define dark theme and custom market colors
    style = mpf.make_mpf_style(base_mpf_style='nightclouds')
    mc = mpf.make_marketcolors(up='green', down='red', inherit=True)

    # Plot chart
    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        style=mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc),
        returnfig=True,
        title='Crypto Chart',
        ylabel='Price'
    )

    # Add faint watermark logo if available
    logo_path = "WellermenLogoTrans.png"
    if os.path.exists(logo_path):
        img = plt.imread(logo_path)
        ax = axlist[0]
        ax.imshow(img, aspect='auto', extent=(0, 1, 0, 1), alpha=0.08,
                  transform=ax.transAxes, zorder=0)

    # Save to buffer
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
