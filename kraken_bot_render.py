import os
import time
import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd
import warnings

warnings.filterwarnings("ignore", category=FutureWarning)

# API keys from Render environment
KRAKEN_API_KEY = os.environ.get("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.environ.get("KRAKEN_API_SECRET")

if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    raise Exception("❌ Missing Kraken API credentials")

# Initialize Kraken API
api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
k = KrakenAPI(api)

# === CONFIG ===
TRADE_PAIRS = [
    ("XBTUSD", "XBT", "USD"),
    ("ETHUSD", "ETH", "USD"),
    ("ADAUSD", "ADA", "USD"),
    ("SOLUSD", "SOL", "USD"),
    ("LTCUSD", "LTC", "USD"),
    ("XRPUSD", "XRP", "USD"),
    ("DOTUSD", "DOT", "USD"),
    ("AVAXUSD", "AVAX", "USD"),
]

MIN_BALANCE_USD = 5.0
TAKE_PROFIT_PCT = 0.02
STOP_LOSS_PCT = 0.01
TRADE_INTERVAL = 60  # seconds

def log(msg):
    print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def get_balance():
    balance = k.get_account_balance()
    return {cur: float(balance.loc[cur]["vol"]) for cur in balance.index}

def get_price(pair):
    try:
        ohlc, _ = k.get_ohlc_data(pair, interval=1)
        return float(ohlc["close"].iloc[-1])
    except Exception as e:
        log(f"❌ Failed to get price for {pair}: {e}")
        return None

def place_order(order_type, pair, volume):
    try:
        api.query_private("AddOrder", {
            "pair": pair,
            "type": order_type,
            "ordertype": "market",
            "volume": str(volume)
        })
    except Exception as e:
        log(f"❌ Order error on {pair}: {e}")

def trade(pair, base_asset, quote_asset):
    balances = get_balance()
    usd_balance = balances.get(quote_asset, 0)
    base_balance = balances.get(base_asset, 0)

    price = get_price(pair)
    if not price:
        return

    if usd_balance > MIN_BALANCE_USD:
        volume = usd_balance / price
        place_order("buy", pair, volume)
        entry_price = price
        log(f"🟢 Bought {volume:.6f} {base_asset} at ${entry_price:.2f}")

        while True:
            time.sleep(TRADE_INTERVAL)
            current_price = get_price(pair)
            if not current_price:
                continue

            change_pct = (current_price - entry_price) / entry_price
            log(f"🔍 Checking price: ${current_price:.2f} | Change: {change_pct:.2%}")

            if change_pct >= TAKE_PROFIT_PCT:
                place_order("sell", pair, volume)
                log(f"💰 Take profit hit: Sold at ${current_price:.2f}")
                break
            elif change_pct <= -STOP_LOSS_PCT:
                place_order("sell", pair, volume)
                log(f"🔻 Stop loss hit: Sold at ${current_price:.2f}")
                break
    else:
        log(f"⚠️ Not enough {quote_asset} to place trade.")

if __name__ == "__main__":
    while True:
        for pair, base, quote in TRADE_PAIRS:
            trade(pair, base, quote)
            log("⏳ Cycle complete. Waiting for reinvest...")
            time.sleep(TRADE_INTERVAL)
