{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyOAi3vMegsjAQnDQ3fjAHFJ",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/Saisrvn/zero--api/blob/main/app.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": null,
      "metadata": {
        "id": "A-Aicoh-kdZT"
      },
      "outputs": [],
      "source": [
        "from flask import Flask, request, jsonify\n",
        "import yfinance as yf\n",
        "import pandas as pd\n",
        "import ta\n",
        "\n",
        "app = Flask(__name__)\n",
        "\n",
        "# 30 allowed stock symbols\n",
        "ALLOWED_SYMBOLS = [\n",
        "    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',\n",
        "    'SBIN.NS', 'WIPRO.NS', 'LT.NS', 'BAJFINANCE.NS', 'HINDUNILVR.NS',\n",
        "    'AXISBANK.NS', 'KOTAKBANK.NS', 'BHARTIARTL.NS', 'ITC.NS', 'ASIANPAINT.NS',\n",
        "    'MARUTI.NS', 'HCLTECH.NS', 'ULTRACEMCO.NS', 'SUNPHARMA.NS', 'TECHM.NS',\n",
        "    'TITAN.NS', 'NESTLEIND.NS', 'POWERGRID.NS', 'ONGC.NS', 'JSWSTEEL.NS',\n",
        "    'COALINDIA.NS', 'NTPC.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'HDFCLIFE.NS'\n",
        "]\n",
        "\n",
        "def get_period_by_interval(interval):\n",
        "    return {\n",
        "        '1m': '7d',\n",
        "        '5m': '60d',\n",
        "        '15m': '60d',\n",
        "        '30m': '60d',\n",
        "        '60m': '60d',\n",
        "        '1h': '60d',\n",
        "        '1d': 'max',\n",
        "        '1wk': 'max',\n",
        "        '1mo': 'max'\n",
        "    }.get(interval, 'max')\n",
        "\n",
        "def calculate_indicators(df):\n",
        "    df['SMA_18'] = df['Close'].rolling(window=18).mean()\n",
        "    df['Volume_Avg'] = df['Volume'].rolling(window=18).mean()\n",
        "    df['Volume_Spike'] = df['Volume'] > df['Volume_Avg'] * 1.5\n",
        "\n",
        "    smi = ta.momentum.StochasticOscillator(close=df['Close'], high=df['High'], low=df['Low'])\n",
        "    df['SMI'] = smi.stoch_signal()\n",
        "\n",
        "    df['Pivot'] = (df['High'] + df['Low'] + df['Close']) / 3\n",
        "    df['BC'] = (df['High'] + df['Low']) / 2\n",
        "    df['TC'] = 2 * df['Pivot'] - df['BC']\n",
        "\n",
        "    df['SMA_Cross'] = df['Close'] > df['SMA_18']\n",
        "    df['CPR_Breakout'] = df.apply(lambda row: (\n",
        "        'Above TC' if row['Close'] > row['TC'] else\n",
        "        'Below BC' if row['Close'] < row['BC'] else\n",
        "        'Inside CPR'\n",
        "    ), axis=1)\n",
        "\n",
        "    return df\n",
        "\n",
        "@app.route('/stock_data')\n",
        "def stock_data():\n",
        "    symbol = request.args.get('symbol', '').upper()\n",
        "    interval = request.args.get('interval', '1d')\n",
        "    period = get_period_by_interval(interval)\n",
        "\n",
        "    if symbol not in ALLOWED_SYMBOLS:\n",
        "        return jsonify({'error': 'Stock not allowed'}), 403\n",
        "\n",
        "    df = yf.download(tickers=symbol, period=period, interval=interval)\n",
        "    if df.empty:\n",
        "        return jsonify({'error': 'No data found'}), 404\n",
        "\n",
        "    df.dropna(inplace=True)\n",
        "    df = calculate_indicators(df)\n",
        "    df.reset_index(inplace=True)\n",
        "\n",
        "    if 'Datetime' in df.columns:\n",
        "         df.rename(columns={'Datetime': 'Date'}, inplace=True)\n",
        "    df = df[[\n",
        "    'Date', 'Open', 'High', 'Low', 'Close', 'Volume',\n",
        "    'SMA_18', 'SMI', 'Pivot', 'TC', 'BC',\n",
        "    'Volume_Avg', 'Volume_Spike', 'SMA_Cross', 'CPR_Breakout'\n",
        "     ]].dropna()\n",
        "\n",
        "    df.rename(columns={'Datetime': 'Date'}, inplace=True)\n",
        "    df['Date'] = df['Date'].astype(str)\n",
        "\n",
        "    return jsonify(df.to_dict(orient='records'))\n",
        "\n",
        "if __name__ == '__main__':\n",
        "    app.run(debug=True)\n"
      ]
    }
  ]
}