# Candlestick chart for NIFTY50 using mplfinance (daily OHLC)

import mysql.connector
import pandas as pd
import mplfinance as mpf

# Connect to MySQL
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'nifty100'
}

conn = mysql.connector.connect(**config)
print("Connected to MySQL.")

#  Load raw 5-minute data for NIFTY50
query = """
SELECT date AS Date, open AS Open, high AS High, low AS Low, close AS Close, volume AS Volume
FROM nifty50_5m where date like '2025%'
ORDER BY date
"""

df = pd.read_sql(query, conn)
conn.close()

# Convert 'Date' to datetime and set as index
df['Date'] = pd.to_datetime(df['Date'])
df.set_index('Date', inplace=True)

print(f"Loaded {len(df)} 5-minute rows for NIFTY50.")

# Resample to daily OHLCV (candlestick data)
daily = df.resample('D').agg({
    'Open':  'first',
    'High':  'max',
    'Low':   'min',
    'Close': 'last',
    'Volume': 'sum'
})

# Drop any full-NaN days (non-trading days)
daily = daily.dropna()

print(f"Resampled to {len(daily)} daily candles.")

# Create Candlestick Chart

mpf.plot(
    daily,
    type='candle',
    style='yahoo',            
    title='NIFTY50 Daily- 2025 Candlestick Chart',
    ylabel='Price',
    volume=True,               
    figsize=(12, 8),           
    mav=(20, 50),            
    show_nontrading=False     
)

print("Candlestick chart displayed.")