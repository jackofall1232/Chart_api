from flask import Flask, request, send_file import mplfinance as mpf import pandas as pd import matplotlib.pyplot as plt import numpy as np import io import os

app = Flask(name)

@app.route('/chart', methods=['POST']) def chart(): data = request.json

# Prepare DataFrame
df = pd.DataFrame(data['ohlc'])
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp', inplace=True)
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

# Style setup
mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
custom_style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

# Addplots (e.g., Bollinger Bands)
add_plots = []
if 'upper' in data and 'lower' in data:
    add_plots += [
        mpf.make_addplot(data['upper'], color='blue'),
        mpf.make_addplot(data['lower'], color='blue')
    ]

# Main plot
fig, axlist = mpf.plot(
    df,
    type='candle',
    style=custom_style,
    title=f"{data.get('symbol', 'Crypto')} - {data.get('interval', '')} Chart",
    ylabel='Price',
    returnfig=True,
    hlines=dict(hlines=data.get("support", []), colors='red'),
    addplot=add_plots
)

# Optional: Annotate Doji
if data.get("candles", {}).get("highlight_patterns"):
    ax = axlist[0]
    for i, row in df.iterrows():
        if abs(row["Open"] - row["Close"]) < 0.1:
            ax.annotate("★", (i, row["High"] + 1), color='yellow', ha='center', fontsize=9)

# Watermark overlay
logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
if os.path.exists(logo_path):
    try:
        img = plt.imread(logo_path)
        ax = axlist[0]
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        ax.imshow(img, extent=(x_min, x_max, y_min, y_max), alpha=0.08, aspect='auto', zorder=-1)
    except Exception as e:
        print(f"Watermark error: {e}")

# Output buffer
buf = io.BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=False)
buf.seek(0)
return send_file(buf, mimetype='image/png')

if name == 'main': app.run(host='0.0.0.0', port=10000, debug=True)

