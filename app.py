from flask import Flask, request, send_file import mplfinance as mpf import pandas as pd import matplotlib.pyplot as plt import numpy as np import io import os

app = Flask(name)

@app.route('/chart', methods=['POST']) def chart(): # Get JSON data from request data = request.json

# Create DataFrame from OHLC data
df = pd.DataFrame(data["ohlc"])
df.index = pd.to_datetime(df["timestamp"])
df = df[["Open", "High", "Low", "Close", "Volume"]]

# Calculate Bollinger Bands
df['MA20'] = df['Close'].rolling(window=20).mean()
df['Upper'] = df['MA20'] + 2 * df['Close'].rolling(window=20).std()
df['Lower'] = df['MA20'] - 2 * df['Close'].rolling(window=20).std()

# Detect doji candles
df['is_doji'] = abs(df['Open'] - df['Close']) < (df['High'] - df['Low']) * 0.1

# Prepare dark theme and market colors
style = mpf.make_mpf_style(base_mpf_style='nightclouds')
mc = mpf.make_marketcolors(up='green', down='red', inherit=True)

# Additional plots: Bollinger bands
apds = [
    mpf.make_addplot(df['Upper'], color='gray'),
    mpf.make_addplot(df['Lower'], color='gray'),
    mpf.make_addplot(df['MA20'], color='orange')
]

# Create the figure and axes
fig, axlist = mpf.plot(
    df,
    type='candle',
    mav=data.get("ema", []),
    hlines=dict(hlines=data.get("support", []), colors='red'),
    addplot=apds,
    style=mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc),
    returnfig=True,
    title='SOL/USDT - 4H Chart',
    ylabel='Price'
)

# Plot Doji markers
ax = axlist[0]
for i, is_doji in enumerate(df['is_doji']):
    if is_doji:
        ax.plot(df.index[i], df['Close'][i], marker='*', color='yellow', markersize=8, zorder=10)

# Add watermark logo if it exists
logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
if os.path.exists(logo_path):
    try:
        img = plt.imread(logo_path)
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        ax.imshow(
            img,
            extent=(x_min, x_max, y_min, y_max),
            alpha=0.08,
            aspect='auto',
            zorder=-1
        )
    except Exception as e:
        print(f"Error adding watermark: {e}")

# Export image
buf = io.BytesIO()
fig.savefig(buf, format='png', bbox_inches='tight', dpi=150, transparent=False)
buf.seek(0)
return send_file(buf, mimetype='image/png')

if name == 'main': app.run(host='0.0.0.0', port=10000, debug=True)

