from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import os
import traceback

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    try:
        data = request.json

        # Debug incoming data (optional)
        # print("Incoming JSON:", json.dumps(data)[:500])

        # Prepare DataFrame from direct array (no 'candles' key)
        if not data or not isinstance(data, list):
            raise ValueError("Invalid JSON: Expected an array of OHLCV data")
        df = pd.DataFrame(data)
        if df.empty:
            return "Error: Empty OHLC data", 400

        # Rename 'timestamp' to 'time' if needed
        df.rename(columns={'timestamp': 'time'}, inplace=True)
        if 'time' not in df.columns:
            raise ValueError("Missing 'time' or 'timestamp' column in data")

        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)

        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")
        df = df[required_cols]
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']  # Rename for mplfinance
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

        # Main plot (candlestick chart)
        fig, axlist = mpf.plot(
            df,
            type='candle',  # Ensures candlestick rendering
            style=custom_style,
            title=f"{data[0].get('symbol', 'Crypto')} - 4H Chart",
            ylabel='Price',
            returnfig=True,
            hlines=dict(hlines=data[0].get('support', []), colors='red'),
            addplot=add_plots,
            datetime_format='%Y-%m-%d %H:%M:%S',
            figsize=(12, 6),
            figscale=1.5,
            tight_layout=False
        )

        # Optional: Annotate Doji
        if data[0].get("highlight_patterns"):
            ax = axlist[0]
            for i, row in df.iterrows():
                candle_range = row["High"] - row["Low"]
                if candle_range > 0 and abs(row["Open"] - row["Close"]) < 0.1 * candle_range:
                    ax.annotate("★", (i, row["High"] + 0.5 * candle_range), color='yellow', ha='center', fontsize=9)

        # Watermark overlay
        logo_path = os.path.join(os.path.dirname(__file__), 'Chart_api', 'WellermenLogoTrans.png')
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
        fig.savefig(buf, format='png', dpi=150, transparent=False)
        plt.close(fig)
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    except KeyError as e:
        print(f"KeyError: {str(e)}\n{traceback.format_exc()}")
        return f"Error: Missing key in JSON data - {e}", 400
    except Exception as e:
        print(f"Error: {str(e)}\n{traceback.format_exc()}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
