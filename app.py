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

    # Prepare DataFrame
    try:
        df = pd.DataFrame(data['candles'])  # Use 'candles' from JSON
        if df.empty:
            return "Error: Empty OHLC data", 400
        df['time'] = pd.to_datetime(df['time'])  # Use 'time' from JSON
        df.set_index('time', inplace=True)
        df = df[['open', 'high', 'low', 'close', 'volume']]  # Match JSON keys
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']  # Rename for mplfinance

        # Validate data
        if len(df) < 1:
            return "Error: Insufficient data", 400
        print(f"DataFrame shape: {df.shape}, Columns: {df.columns.tolist()}")  # Debug

        # Calculate Bollinger Bands (20-period SMA, 2 std dev)
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['SMA'] + (df['STD'] * 2)
        df['Lower'] = df['SMA'] - (df['STD'] * 2)
        add_plots = [
            mpf.make_addplot(df['Upper'], color='blue', linestyle='--'),
            mpf.make_addplot(df['Lower'], color='blue', linestyle='--')
        ]

        # Style setup
        mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
        custom_style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

        # Main plot
        fig, axlist = mpf.plot(
            df,
            type='candle',
            style=custom_style,
            title=f"{data.get('symbol', 'Crypto')} - 4H Chart",
            ylabel='Price',
            returnfig=True,
            hlines=dict(hlines=data.get("support", []), colors='red'),
            addplot=add_plots,
            datetime_format='%Y-%m-%d %H:%M',
            figsize=(12, 6),  # Explicit figure size
            figscale=1.5,     # Scale up chart
            tight_layout=False  # Avoid compression
        )

        # Optional: Annotate Doji
        if data.get("candles", {}).get("highlight_patterns"):
            ax = axlist[0]
            for i, row in df.iterrows():
                candle_range = row["High"] - row["Low"]
                if candle_range > 0 and abs(row["Open"] - row["Close"]) < 0.1 * candle_range:
                    ax.annotate("★", (i, row["High"] + 0.5 * candle_range), color='yellow', ha='center', fontsize=9)

        # Watermark overlay
        logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
        if os.path.exists(logo_path):
            try:
                img = plt.imread(logo_path)
                ax = axlist[0]
                x_min, x_max = ax.get_xlim()
                y_min, y_max = ax.get_ylim()
                ax.imshow(img, extent=(x_min, x_max, y_min, y_max), alpha=0.08, aspect='auto', zorder=-1)
                print("Watermark added")
            except Exception as e:
                print(f"Watermark error: {e}")
        else:
            print(f"Logo file not found at: {logo_path}")

        # Output buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches=None, dpi=150, transparent=False)
        plt.close(fig)  # Close figure to free memory
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    except KeyError as e:
        return f"Error: Missing key in JSON data - {e}", 400
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
