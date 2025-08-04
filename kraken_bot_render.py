import time
from kraken_api import KrakenAPI

# === API Setup ===
api = KrakenAPI()

# === CONFIG ===
TRADE_PAIRS = [
    ("XXBTZUSD", "XBT", "USD"),
    ("XETHZUSD", "ETH", "USD"),
    ("ADAUSD", "ADA", "USD"),
    ("SOLUSD", "SOL", "USD"),
    ("XLTCZUSD", "LTC", "USD"),
    ("XXRPZUSD", "XRP", "USD"),
    ("DOTUSD", "DOT", "USD"),
    ("AVAXUSD", "AVAX", "USD")
]

MIN_BALANCE_USD = 5.0
TAKE_PROFIT_PCT = 0.02
STOP_LOSS_PCT = 0.01
TRADE_INTERVAL = 60  # seconds

def log(msg):
    print(f"[LOG] {time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

def get_balance():
    balance = api.get_account_balance()
    return {cur: float(balance[cur]["vol"]) for cur in balance}

def get_price(pair):
    try:
        ohlc, _ = api.get_ohlc_data(pair, interval=1)
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

def trade():
    balances = get_balance()

    for pair, base, quote in TRADE_PAIRS:
        log(f"🔄 Starting trade cycle for {pair}")
        time.sleep(1.5)  # Prevent Kraken rate limit

        usd_balance = balances.get(quote, 0)
        base_balance = balances.get(base, 0)

        price = get_price(pair)
        if price is None:
            continue

        if usd_balance > MIN_BALANCE_USD:
            volume = usd_balance / price
            place_order("buy", pair, volume)
            entry_price = price
            log(f"🟢 Bought {volume:.6f} {base} at ${entry_price:.2f}")

            while True:
                time.sleep(TRADE_INTERVAL)
                current_price = get_price(pair)
                if current_price is None:
                    continue
                change_pct = (current_price - entry_price) / entry_price
                log(f"🔍 {pair} @ ${current_price:.2f} | Change: {change_pct:.2%}")

                if change_pct >= TAKE_PROFIT_PCT:
                    place_order("sell", pair, volume)
                    log(f"💰 Take profit hit: Sold at ${current_price:.2f}")
                    break
                elif change_pct <= -STOP_LOSS_PCT:
                    place_order("sell", pair, volume)
                    log(f"🔻 Stop loss hit: Sold at ${current_price:.2f}")
                    break
        else:
            log(f"⚠️ Not enough {quote} to trade {pair}.")

if __name__ == "__main__":
    while True:
        trade()
        log("⏳ Cycle complete. Waiting for reinvest...")
        time.sleep(TRADE_INTERVAL)
