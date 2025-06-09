from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
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
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    macd_df = pd.DataFrame({
        'MACD': macd_line,
        'Signal': signal_line,
        'Hist': macd_hist
    }, index=df.index)

    # Custom style
    mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
    style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

    # MACD addplot
    macd_ap = [
        mpf.make_addplot(macd_df['MACD'], panel=1, color='cyan', width=1),
        mpf.make_addplot(macd_df['Signal'], panel=1, color='magenta', width=1),
        mpf.make_addplot(macd_df['Hist'], type='bar', panel=1, color='lime', alpha=0.4)
    ]

    # Plot chart
    fig, axlist = mpf.plot(
        df,
        type='candle',
        style=style,
        mav=data.get("ema", []),
        hlines=dict(hlines=data.get("support", []), colors='red'),
        addplot=macd_ap,
        returnfig=True,
        figsize=(10, 6),
        title='SOL/USDT – 2H Chart',
        ylabel='Price',
        ylabel_lower='MACD'
    )

    # Add watermark logo
    logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
    if os.path.exists(logo_path):
        try:
            img = plt.imread(logo_path)
            ax = axlist[0]  # main price chart
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            ax.imshow(img, extent=(x_min, x_max, y_min, y_max), alpha=0.05, aspect='auto', zorder=-1)
        except Exception as e:
            print(f"Logo overlay error: {e}")

    # Output image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
