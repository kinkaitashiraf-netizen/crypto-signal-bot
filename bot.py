import ccxt
import pandas as pd
import requests
import time
from datetime import datetime

# === CONFIGURATION ===
API_TOKEN = 8248706810:AAH12ZmMyIK4e1sSvyP7j2PrTGCiZKnya8k
CHAT_ID = :6605794067
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]  # Add more if you like
TIMEFRAME = "15m"
INTERVAL = 60  # seconds between checks
LIMIT = 100

# === TELEGRAM MESSAGE FUNCTION ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

# === EXCHANGE SETUP ===
exchange = ccxt.binance({'enableRateLimit': True})

def get_data(symbol):
    bars = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=LIMIT)
    df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

def get_signal(df, symbol):
    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=21).mean()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]
    signal = None
    if last['ema_fast'] > last['ema_slow'] and last['rsi'] < 70:
        signal = f"🟢 BUY signal for {symbol}\nRSI: {last['rsi']:.2f}"
    elif last['ema_fast'] < last['ema_slow'] and last['rsi'] > 30:
        signal = f"🔴 SELL signal for {symbol}\nRSI: {last['rsi']:.2f}"
    return signal

send_telegram_message(f"🚀 Bot started for {', '.join(SYMBOLS)} ({TIMEFRAME})")

while True:
    try:
        for symbol in SYMBOLS:
            df = get_data(symbol)
            signal = get_signal(df, symbol)
            now = datetime.now().strftime('%H:%M:%S')
            if signal:
                print(f"[{now}] {signal}")
                send_telegram_message(signal)
            else:
                print(f"[{now}] {symbol}: No clear signal.")
        time.sleep(INTERVAL)
    except Exception as e:
        print("Error:", e)
        time.sleep(60)
