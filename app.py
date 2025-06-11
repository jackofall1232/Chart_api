@app.route('/chart', methods=['POST'])
def chart():
    try:
        raw_input = request.json

        # 🔁 NEW: Support remote file_url (e.g. Dropbox)
        if 'file_url' in raw_input:
            import requests
            file_url = raw_input['file_url']
            r = requests.get(file_url)
            if r.status_code != 200:
                raise ValueError("Failed to download remote file.")
            try:
                json_data = r.json()
            except Exception:
                raise ValueError("Invalid JSON in downloaded file.")
            data = json_data.get('candles', json_data)
        else:
            data = raw_input.get('candles', raw_input)

        if not data or not isinstance(data, list):
            raise ValueError("Invalid JSON: Expected an array of OHLCV data")

        app.logger.info("Received %d entries", len(data))

        df = pd.DataFrame(data)
        if df.empty:
            return "Error: Empty OHLC data", 400

        app.logger.info("Raw DataFrame: %s", df.head(2).to_dict())

        df.rename(columns={'timestamp': 'time'}, inplace=True)
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df.set_index('time', inplace=True)

        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns: {required_cols}")

        df = df[required_cols]
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        # Bollinger Bands
        df['SMA'] = df['Close'].rolling(window=20).mean()
        df['STD'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['SMA'] + (df['STD'] * 2)
        df['Lower'] = df['SMA'] - (df['STD'] * 2)
        add_plots = [
            mpf.make_addplot(df['Upper'], color='blue', linestyle='--'),
            mpf.make_addplot(df['Lower'], color='blue', linestyle='--')
        ]

        mc = mpf.make_marketcolors(up='green', down='red', inherit=True)
        custom_style = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc)

        fig, axlist = mpf.plot(
            df,
            type='candle',
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

        if data[0].get("highlight_patterns"):
            ax = axlist[0]
            for i, row in df.iterrows():
                candle_range = row["High"] - row["Low"]
                if candle_range > 0 and abs(row["Open"] - row["Close"]) < 0.1 * candle_range:
                    ax.annotate("★", (i, row["High"] + 0.5 * candle_range), color='yellow', ha='center', fontsize=9)

        logo_path = os.path.join(os.path.dirname(__file__), 'WellermenLogoTrans.png')
        if os.path.exists(logo_path):
            try:
                img = plt.imread(logo_path)
                ax = axlist[0]
                x_min, x_max = ax.get_xlim()
                y_min, y_max = ax.get_ylim()
                ax.imshow(img, extent=(x_min, x_max, y_min, y_max), alpha=0.08, aspect='auto', zorder=-1)
            except Exception as e:
                app.logger.error("Watermark error: %s", e)

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, transparent=False)
        plt.close(fig)
        buf.seek(0)
        return send_file(buf, mimetype='image/png')

    except Exception as e:
        app.logger.error("Error: %s\n%s", str(e), traceback.format_exc())
        return f"Error: {str(e)}", 500
