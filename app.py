from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    data = request.json

    df = pd.DataFrame(data["ohlc"])
    df.index = pd.to_datetime(df["timestamp"])
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    # Style: dark background, red/green candles
    mc = mpf.make_marketcolors(
        up='green', down='red',
        edge='inherit', wick={'up': 'white', 'down': 'white'},
        volume='in'
    )
    s = mpf.make_mpf_style(
        base_mpf_style='nightclouds',
        marketcolors=mc,
        facecolor='#0F111A',
        edgecolor='white',
        gridstyle=':',
        figcolor='#0F111A',
        rc={'font.size': 10}
    )

    # Generate the candlestick chart
    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        style=s,
        returnfig=True,
        title=data.get("symbol", "Crypto Chart")
    )

    # Add faint logo watermark
    try:
        ax = axlist[0]
        logo = mpimg.imread("WellermenLogoTrans.png")
        ax.imshow(
            logo,
            aspect='auto',
            extent=[*ax.get_xlim(), *ax.get_ylim()],
            alpha=0.06,
            zorder=-10,
            interpolation='bilinear'
        )
    except Exception as e:
        print("Logo overlay failed:", e)

    # Save image to memory
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
