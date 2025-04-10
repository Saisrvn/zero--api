from flask import Flask, request, jsonify
import yfinance as yf
import pandas as pd
import ta

app = Flask(__name__)

# 30 allowed stock symbols
ALLOWED_SYMBOLS = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'WIPRO.NS', 'LT.NS', 'BAJFINANCE.NS', 'HINDUNILVR.NS',
    'AXISBANK.NS', 'KOTAKBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'ASIANPAINT.NS',
    'MARUTI.NS', 'HCLTECH.NS', 'ULTRACEMCO.NS', 'SUNPHARMA.NS', 'TECHM.NS',
    'TITAN.NS', 'NESTLEIND.NS', 'POWERGRID.NS', 'ONGC.NS', 'JSWSTEEL.NS',
    'COALINDIA.NS', 'NTPC.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'HDFCLIFE.NS'
]

def get_period_by_interval(interval):
    return {
        '1m': '7d',
        '5m': '60d',
        '15m': '60d',
        '30m': '60d',
        '60m': '60d',
        '1h': '60d',
        '1d': 'max',
        '1wk': 'max',
        '1mo': 'max'
    }.get(interval, 'max')

def calculate_indicators(df):
    df['SMA_18'] = df['Close'].rolling(window=18).mean()
    df['Volume_Avg'] = df['Volume'].rolling(window=18).mean()
    df['Volume_Spike'] = df['Volume'] > df['Volume_Avg'] * 1.5

    smi = ta.momentum.StochasticOscillator(close=df['Close'], high=df['High'], low=df['Low'])
    df['SMI'] = smi.stoch_signal()

    df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['BC'] = (df['High'] + df['Low']) / 2
    df['TC'] = 2 * df['Pivot'] - df['BC']

    df['SMA_Cross'] = df['Close'] > df['SMA_18']
    df['CPR_Breakout'] = df.apply(lambda row: (
        'Above TC' if row['Close'] > row['TC'] else
        'Below BC' if row['Close'] < row['BC'] else
        'Inside CPR'
    ), axis=1)

    return df

@app.route('/stock_data')
def stock_data():
    symbol = request.args.get('symbol', '').upper()
    interval = request.args.get('interval', '1d')
    period = get_period_by_interval(interval)

    if symbol not in ALLOWED_SYMBOLS:
        return jsonify({'error': 'Stock not allowed'}), 403

    df = yf.download(tickers=symbol, period=period, interval=interval)
    if df.empty:
        return jsonify({'error': 'No data found'}), 404

    df.dropna(inplace=True)
    df = calculate_indicators(df)
    df.reset_index(inplace=True)

    df = df[[
        'Datetime' if 'Datetime' in df.columns else 'Date',
        'Open', 'High', 'Low', 'Close', 'Volume',
        'SMA_18', 'SMI', 'Pivot', 'TC', 'BC',
        'Volume_Avg', 'Volume_Spike', 'SMA_Cross', 'CPR_Breakout'
    ]].dropna()

    df.rename(columns={'Datetime': 'Date'}, inplace=True)
    df['Date'] = df['Date'].astype(str)

    return jsonify(df.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
