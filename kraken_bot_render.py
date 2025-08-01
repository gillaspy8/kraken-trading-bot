
import os
import time
import krakenex
from pykrakenapi import KrakenAPI

# Read API keys from environment variables
api_key = os.getenv("KRAKEN_API_KEY")
private_key = os.getenv("KRAKEN_PRIVATE_KEY")

if not api_key or not private_key:
    raise Exception("Missing API keys. Set KRAKEN_API_KEY and KRAKEN_PRIVATE_KEY in environment variables.")

k = krakenex.API(key=api_key, secret=private_key)
api = KrakenAPI(k)

# Settings
pair = 'XXBTZUSD'  # Bitcoin/USD
trade_amount = 0.001  # BTC amount per trade
profit_target_pct = 1.5  # % profit target
stop_loss_pct = 0.8  # % stop loss
polling_interval = 60  # seconds

def get_price():
    ohlc, _ = api.get_ohlc_data(pair, interval=1)
    return float(ohlc['close'].iloc[-1])

def place_order(order_type, volume):
    response = k.query_private('AddOrder', {
        'pair': pair,
        'type': order_type,
        'ordertype': 'market',
        'volume': volume,
    })
    return response

print("Bot is running...")

entry_price = None
position_open = False

while True:
    try:
        current_price = get_price()
        print(f"Current BTC/USD price: ${current_price:.2f}")

        if not position_open:
            print("Placing BUY order...")
            place_order('buy', trade_amount)
            entry_price = current_price
            position_open = True
        else:
            change_pct = ((current_price - entry_price) / entry_price) * 100

            if change_pct >= profit_target_pct:
                print("Profit target hit. Selling...")
                place_order('sell', trade_amount)
                position_open = False
            elif change_pct <= -stop_loss_pct:
                print("Stop loss hit. Selling...")
                place_order('sell', trade_amount)
                position_open = False
            else:
                print(f"Holding... {change_pct:.2f}% change since entry")

    except Exception as e:
        print("Error:", e)

    time.sleep(polling_interval)
