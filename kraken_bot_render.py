import os
import time
import warnings
import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd

# Suppress 'T' frequency warning
warnings.filterwarnings("ignore", category=FutureWarning, module="pykrakenapi")

# API keys from Render environment
KRAKEN_API_KEY = os.environ.get("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.environ.get("KRAKEN_API_SECRET")

if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    raise Exception("❌ Missing Kraken API credentials. Set KRAKEN_API_KEY and KRAKEN_API_SECRET in environment.")

api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
k = KrakenAPI(api)

# Config
COIN_PAIRS = {
    "XBTUSD": ("XBT", "USD"),
    "ETHUSD": ("ETH", "USD"),
    "SOLUSD": ("SOL", "USD"),
    "ADAUSD": ("ADA", "USD"),
    "AVAXUSD": ("AVAX", "USD"),
    "MATICUSD": ("MATIC", "USD"),
    "DOTUSD": ("DOT", "USD"),
    "ATOMUSD": ("ATOM", "USD")
}

TRADE_INTERVAL = 60  # in seconds
TAKE_PROFIT_PCT = 0.02
STOP_LOSS_PCT = 0.01
MIN_USD_BALANCE = 5.0

entry_prices = {}

def log(msg):
    print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def get_balance():
    try:
        balance = k.get_account_balance()
        return {key: float(balance.loc[key]["vol"]) for key in balance.index}
    except Exception as e:
        log(f"❌ Error fetching balance: {e}")
        return {}

def get_price(pair):
    try:
        ohlc, _ = k.get_ohlc_data(pair, interval=1)
        return float(ohlc["close"].iloc[-1])
    except Exception as e:
        log(f"❌ Error fetching price for {pair}: {e}")
        return None

def place_order(pair, order_type, volume):
    try:
        log(f"📈 Placing {order_type.upper()} order for {volume:.6f} on {pair}")
        api.query_private("AddOrder", {
            "pair": pair,
            "type": order_type,
            "ordertype": "market",
            "volume": str(volume)
        })
    except Exception as e:
        log(f"❌ Order failed for {pair}: {e}")

def trade(pair, base_asset, trade_asset):
    balances = get_balance()
    price = get_price(pair)
    if price is None:
        return

    usd_balance = balances.get(base_asset, 0)
    coin_balance = balances.get(trade_asset, 0)

    if coin_balance > 0 and pair in entry_prices:
        current_price = price
        entry_price = entry_prices[pair]
        change = (current_price - entry_price) / entry_price

        log(f"📊 {pair}: Entry ${entry_price:.2f}, Now ${current_price:.2f} ({change*100:.2f}%)")

        if change >= TAKE_PROFIT_PCT:
            place_order(pair, "sell", coin_balance)
            log(f"✅ TAKE PROFIT on {pair} at ${current_price:.2f}")
            del entry_prices[pair]
        elif change <= -STOP_LOSS_PCT:
            place_order(pair, "sell", coin_balance)
            log(f"🛑 STOP LOSS on {pair} at ${current_price:.2f}")
            del entry_prices[pair]

    elif usd_balance >= MIN_USD_BALANCE:
        volume = usd_balance / price / len(COIN_PAIRS)
        place_order(pair, "buy", volume)
        entry_prices[pair] = price
        log(f"🟢 BOUGHT {volume:.6f} {trade_asset} of {pair} at ${price:.2f}")

if __name__ == "__main__":
    while True:
        for pair, (coin, base) in COIN_PAIRS.items():
            trade(pair, base, coin)
        time.sleep(TRADE_INTERVAL)
