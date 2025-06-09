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

    # Create custom style
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

    # Create figure with returnfig=True to get Axes object
    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        style=s,
        returnfig=True,
        title=data.get("symbol", "Crypto Chart")
    )

    # Load and overlay logo as faint background
    try:
        ax = axlist[0]
        logo = mpimg.imread("https://www.dropbox.com/scl/fi/pde8rely2bpynxkpkam8a/WellermenlogoTransp.png?raw=1")
        ax.imshow(logo, extent=ax.get_xlim() + ax.get_ylim(),
                  aspect='auto', alpha=0.1, zorder=-10)
    except Exception as e:
        print("Logo overlay failed:", e)

    # Save figure to memory
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)

    return send_file(buf, mimetype='image/png')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
