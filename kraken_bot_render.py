import os
import time
import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd

# Environment variables for API credentials
KRAKEN_API_KEY = os.environ.get("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.environ.get("KRAKEN_API_SECRET")

if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    raise Exception("❌ Missing Kraken API credentials. Set KRAKEN_API_KEY and KRAKEN_API_SECRET in Render.")

# Initialize Kraken API
api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
k = KrakenAPI(api)

# Configuration
TRADE_PAIR = "XBTUSD"
BASE_ASSET = "USD"
TRADE_ASSET = "XBT"
MIN_BALANCE_USD = 5.0
TAKE_PROFIT_PCT = 0.02   # 2% profit
STOP_LOSS_PCT = 0.01     # 1% loss
TRADE_INTERVAL = 60      # Check every 60 seconds

def log(msg):
    print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def get_balance():
    balance = k.get_account_balance()
    usd = float(balance.loc[BASE_ASSET]["vol"]) if BASE_ASSET in balance.index else 0
    xbt = float(balance.loc[TRADE_ASSET]["vol"]) if TRADE_ASSET in balance.index else 0
    return usd, xbt

def get_price():
    ohlc, _ = k.get_ohlc_data(TRADE_PAIR, interval=1)
    return float(ohlc["close"].iloc[-1])

def place_order(order_type, volume):
    try:
        log(f"Placing {order_type.upper()} order for {volume:.6f} {TRADE_ASSET}")
        api.query_private("AddOrder", {
            "pair": TRADE_PAIR,
            "type": order_type,
            "ordertype": "market",
            "volume": str(volume)
        })
    except Exception as e:
        log(f"Order error: {e}")

def trade():
    usd_balance, xbt_balance = get_balance()
    price = get_price()

    if usd_balance > MIN_BALANCE_USD:
        volume = usd_balance / price
        place_order("buy", volume)
        entry_price = price
        log(f"Bought {volume:.6f} {TRADE_ASSET} at ${price:.2f}")

        while True:
            time.sleep(TRADE_INTERVAL)
            current_price = get_price()
            change_pct = (current_price - entry_price) / entry_price

            if change_pct >= TAKE_PROFIT_PCT:
                place_order("sell", volume)
                log(f"💰 Take profit hit: Sold at ${current_price:.2f}")
                break
            elif change_pct <= -STOP_LOSS_PCT:
                place_order("sell", volume)
                log(f"🔻 Stop loss hit: Sold at ${current_price:.2f}")
                break
    else:
        log("Not enough USD to place trade.")

if __name__ == "__main__":
    while True:
        trade()
        log("Waiting to reinvest profits...")
        time.sleep(TRADE_INTERVAL)
