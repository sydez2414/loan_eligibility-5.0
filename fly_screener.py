import os
import pandas as pd
from dotenv import load_dotenv
from binance.client import Client
from binance.exceptions import BinanceAPIException
import ta

# Load API dari .env
load_dotenv()
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_SECRET_KEY")

# Setup Binance Client
client = Client(api_key, api_secret)

def get_usdt_symbols(limit=100):
    try:
        tickers = client.get_ticker()  # Betul method Binance SDK sekarang
        symbols = [x['symbol'] for x in tickers if x['symbol'].endswith('USDT') and not x['symbol'].endswith('BUSD')]
        return symbols[:limit]
    except Exception as e:
        print(f"❌ Error fetching tickers: {e}")
        return []

def get_klines(symbol, interval='1h', limit=100):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        return df
    except BinanceAPIException as e:
        print(f"❌ Binance API error for {symbol}: {e}")
        return None

def check_fly_signal(df):
    df['ema7'] = ta.trend.ema_indicator(df['close'], window=7)
    df['ema21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)

    last = df.iloc[-1]

    # Syarat nak fly
    if (
        last['ema7'] > last['ema21'] and
        df['ema7'].iloc[-2] < df['ema21'].iloc[-2] and
        last['rsi'] < 40
    ):
        return True
    return False

def main():
    print("🔎 Screener running... Sabar jap bro...\n")
    coins_to_check = get_usdt_symbols()
    fly_list = []

    for symbol in coins_to_check:
        df = get_klines(symbol)
        if df is not None and not df.empty:
            if check_fly_signal(df):
                fly_list.append(symbol)

    print("🚀 Coin yang mungkin nak fly:", fly_list)

if __name__ == "__main__":
    main()
