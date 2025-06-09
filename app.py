from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    data = request.json

    # Validate required keys
    if not all(k in data for k in ("ohlc", "ema", "support")):
        return {"error": "Missing one or more required keys: 'ohlc', 'ema', 'support'"}, 400

    try:
        df = pd.DataFrame(data["ohlc"])
        df.index = pd.to_datetime(df["timestamp"])
        df = df[["Open", "High", "Low", "Close", "Volume"]]
    except Exception as e:
        return {"error": f"Invalid OHLC format or timestamp: {str(e)}"}, 400

    # Custom style
    style = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        rc={'axes.labelcolor': 'white', 'xtick.color': 'white', 'ytick.color': 'white'},
        marketcolors=mpf.make_marketcolors(up='green', down='red')
    )

    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        returnfig=True,
        style=style,
        title='Crypto Chart'
    )

    # Overlay logo if file exists
    logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
    if os.path.exists(logo_path):
        try:
            logo = mpimg.imread(logo_path)
            ax = axlist[0]
            ax.imshow(
                logo,
                aspect='auto',
                extent=[df.index[0], df.index[-1], df["Low"].min(), df["High"].max()],
                alpha=0.1,
                zorder=0
            )
        except Exception as e:
            print(f"Logo overlay failed: {e}")

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')
