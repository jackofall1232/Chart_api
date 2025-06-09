from flask import Flask, request, send_file
import mplfinance as mpf
import pandas as pd
import io

app = Flask(__name__)

@app.route('/chart', methods=['POST'])
def chart():
    data = request.json
    
    df = pd.DataFrame(data["ohlc"])
    df.index = pd.to_datetime(df["timestamp"])
    df = df[["Open", "High", "Low", "Close", "Volume"]]

    fig = mpf.plot(df, type='candle', mav=data.get("ema", []), hlines=dict(hlines=data.get("support", []), colors='red'),
                   returnfig=True)

    buf = io.BytesIO()
    fig[0].savefig(buf, format='png')
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png')
