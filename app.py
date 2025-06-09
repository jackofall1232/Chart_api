from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
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

    # Define dark theme and custom market colors
    style = mpf.make_mpf_style(base_mpf_style='nightclouds')
    mc = mpf.make_marketcolors(up='green', down='red', inherit=True)

    # Plot candlestick chart with optional EMAs and support lines
    fig, axlist = mpf.plot(
        df,
        type='candle',
        mav=data.get("ema", []),  # Exponential Moving Averages if provided
        hlines=dict(hlines=data.get("support", []), colors='red'),  # Support levels if provided
        style=mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc),
        returnfig=True,
        title='Crypto Chart',
        ylabel='Price'
    )

    # Add watermark logo
    logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
    if os.path.exists(logo_path):
        try:
            # Load the logo image
            img = plt.imread(logo_path)
            
            # Get the main axes (should be the first one since we're only plotting candles)
            ax = axlist[0]
            
            # Use data coordinates to place watermark over the chart area
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            ax.imshow(
                img,
                extent=(x_min, x_max, y_min, y_max),
                alpha=0.08,  # Adjust this value (0.0-1.0) to make watermark more/less visible
                aspect='auto',
                zorder=0  # Places watermark behind chart elements
            )
            print("Watermark added successfully")
        except Exception as e:
            print(f"Error adding watermark: {e}")
    else:
        print(f"Logo file not found at: {logo_path}")

    # Save figure to buffer and return as PNG
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
