import os
import time
import krakenex
from pykrakenapi import KrakenAPI
import pandas as pd

# Load API credentials from environment
KRAKEN_API_KEY = os.environ.get("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.environ.get("KRAKEN_API_SECRET")

if not KRAKEN_API_KEY or not KRAKEN_API_SECRET:
    raise Exception("❌ Missing API credentials. Set them in Render.")

# Initialize Kraken API
api = krakenex.API(key=KRAKEN_API_KEY, secret=KRAKEN_API_SECRET)
k = KrakenAPI(api)

# === CONFIGURATION ===
TRADE_PAIRS = {
    "ETHUSD": {"base": "USD", "asset": "ETH"},
    "XBTUSD": {"base": "USD", "asset": "XBT"},
    "SOLUSD": {"base": "USD", "asset": "SOL"},
    "AVAXUSD": {"base": "USD", "asset": "AVAX"},
    "MATICUSD": {"base": "USD", "asset": "MATIC"},
    "ADAUSD": {"base": "USD", "asset": "ADA"},
    "LINKUSD": {"base": "USD", "asset": "LINK"},
    "DOGEUSD": {"base": "USD", "asset": "DOGE"}
}

MIN_BALANCE_USD = 5.0
TAKE_PROFIT_PCT = 0.02  # 2%
STOP_LOSS_PCT = 0.01    # 1%
TRADE_INTERVAL = 60     # seconds

# === LOGGING ===
def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

# === HELPERS ===
def get_balance():
    balance = k.get_account_balance()
    return {k: float(v["vol"]) for k, v in balance.iterrows()}

def get_price(pair):
    ohlc, _ = k.get_ohlc_data(pair, interval=1)
    return float(ohlc["close"].iloc[-1])

def place_order(pair, order_type, volume):
    try:
        log(f"{order_type.upper()} {volume:.6f} of {pair}")
        api.query_private("AddOrder", {
            "pair": pair,
            "type": order_type,
            "ordertype": "market",
            "volume": str(volume)
        })
    except Exception as e:
        log(f"Order failed: {e}")

# === MAIN TRADING LOGIC ===
def trade_pair(pair, base, asset, balances):
    try:
        price = get_price(pair)
        usd_balance = balances.get(base, 0)
        asset_balance = balances.get(asset, 0)

        # If we hold base currency, buy the asset
        if usd_balance > MIN_BALANCE_USD:
            volume = usd_balance / price
            place_order(pair, "buy", volume)
            log(f"✅ Bought {volume:.6f} {asset} at ${price:.2f}")
            entry_price = price

            while True:
                time.sleep(TRADE_INTERVAL)
                price_now = get_price(pair)
                change_pct = (price_now - entry_price) / entry_price

                if change_pct >= TAKE_PROFIT_PCT:
                    place_order(pair, "sell", volume)
                    log(f"💰 Take profit: Sold {volume:.6f} {asset} at ${price_now:.2f}")
                    break
                elif change_pct <= -STOP_LOSS_PCT:
                    place_order(pair, "sell", volume)
                    log(f"🔻 Stop loss: Sold {volume:.6f} {asset} at ${price_now:.2f}")
                    break

        else:
            log(f"Not enough {base} to buy {asset}. Skipping.")

    except Exception as e:
        log(f"Error in trade_pair {pair}: {e}")

# === RUN LOOP ===
if __name__ == "__main__":
    while True:
        balances = get_balance()
        for pair, info in TRADE_PAIRS.items():
            trade_pair(pair, info["base"], info["asset"], balances)
        log("🔄 Waiting before next trading cycle...\n")
        time.sleep(TRADE_INTERVAL)
