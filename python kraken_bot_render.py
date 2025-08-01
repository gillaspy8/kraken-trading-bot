import os
import krakenex
from pykrakenapi import KrakenAPI
import time
import pandas as pd

# Load API keys from environment variables
API_KEY = os.getenv("KRAKEN_API_KEY")
API_SECRET = os.getenv("KRAKEN_API_SECRET")

if not API_KEY or not API_SECRET:
    raise Exception("❌ Missing Kraken API credentials. Set KRAKEN_API_KEY and KRAKEN_API_SECRET in Render.")

# Initialize Kraken API
api = krakenex.API(key=API_KEY, secret=API_SECRET)
k = KrakenAPI(api)

print("✅ Kraken trading bot initialized with stop-loss and take-profit support.")

# === SETTINGS ===
PAIRS = ['XXBTZUSD', 'XETHZUSD']  # BTC/USD and ETH/USD
INTERVAL = 1  # 1-minute interval
TRADE_VOLUME = {
    'XXBTZUSD': 0.001,
    'XETHZUSD': 0.01
}
STOP_LOSS_PERCENT = 2.0     # 2% stop-loss
TAKE_PROFIT_PERCENT = 5.0   # 5% take-profit

# Track open trades
open_trades = {}

def place_market_buy(pair, volume):
    print(f"🚀 Buying {volume} of {pair}")
    response = api.query_private('AddOrder', {
        'pair': pair.replace('X', '').replace('Z', ''),
        'type': 'buy',
        'ordertype': 'market',
        'volume': str(volume)
    })
    return response

def place_market_sell(pair, volume):
    print(f"💰 Selling {volume} of {pair}")
    response = api.query_private('AddOrder', {
        'pair': pair.replace('X', '').replace('Z', ''),
        'type': 'sell',
        'ordertype': 'market',
        'volume': str(volume)
    })
    return response

# === MAIN LOOP ===
while True:
    try:
        for pair in PAIRS:
            print(f"📈 Checking {pair}...")
            ohlc, _ = k.get_ohlc_data(pair, interval=INTERVAL)
            last_candle = ohlc.iloc[-1]

            close_price = last_candle['close']
            open_price = last_candle['open']
            print(f"🕒 {pair} - Open: {open_price}, Close: {close_price}")

            if pair not in open_trades:
                if close_price > open_price:
                    volume = TRADE_VOLUME.get(pair, 0.001)
                    place_market_buy(pair, volume)
                    open_trades[pair] = {
                        'buy_price': close_price,
                        'volume': volume
                    }
                    print(f"✅ Bought {pair} at {close_price}")
            else:
                trade = open_trades[pair]
                buy_price = trade['buy_price']
                volume = trade['volume']
                stop_loss_price = buy_price * (1 - STOP_LOSS_PERCENT / 100)
                take_profit_price = buy_price * (1 + TAKE_PROFIT_PERCENT / 100)

                if close_price <= stop_loss_price:
                    print(f"🛑 Stop-loss hit for {pair} at {close_price}")
                    place_market_sell(pair, volume)
                    del open_trades[pair]

                elif close_price >= take_profit_price:
                    print(f"🎯 Take-profit hit for {pair} at {close_price}")
                    place_market_sell(pair, volume)
                    del open_trades[pair]

    except Exception as e:
        print("⚠️ Error:", e)

    print("⏳ Waiting 60 seconds...\n")
    time.sleep(60)
