# Rolling Volatility (Heatmap)

import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Connect (same as before)
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='root',
    database='nifty100'
)

# Load daily data 
query = """
SELECT 'NIFTY50' AS index_name, trading_day, avg_close AS daily_close
FROM nifty50_daily
UNION
SELECT 'NIFTY100' AS index_name, trading_day, avg_close AS daily_close
FROM nifty100_daily
ORDER BY index_name, trading_day
"""

daily = pd.read_sql(query, conn)
conn.close()

# Convert date
daily['trading_day'] = pd.to_datetime(daily['trading_day'])

# Calculate daily returns (%)
daily['daily_return'] = daily.groupby('index_name')['daily_close'].pct_change() * 100

# Rolling 30-day volatility (std dev of returns)
window = 30
daily['rolling_volatility'] = daily.groupby('index_name')['daily_return'].transform(
    lambda x: x.rolling(window=window, min_periods=1).std()
)

# Drop rows with NaN volatility (first window-1 days)
daily_vol = daily.dropna(subset=['rolling_volatility'])

print("Volatility sample:")
print(daily_vol[['index_name', 'trading_day', 'daily_return', 'rolling_volatility']].head(15))

# Plot

# Extract year and month
daily_vol['year'] = daily_vol['trading_day'].dt.year
daily_vol['month'] = daily_vol['trading_day'].dt.month_name()

# Pivot: rows = year, columns = month, values = average volatility
monthly_vol = daily_vol.pivot_table(
    index='year',
    columns='month',
    values='rolling_volatility',
    aggfunc='mean'
).round(2)

# Reorder months correctly
month_order = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
monthly_vol = monthly_vol[month_order]

# Plot heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(
    monthly_vol,
    annot=True,           
    fmt='.2f',
    cmap='YlOrRd',    
    linewidths=0.5,
    cbar_kws={'label': 'Average Rolling Volatility (%)'}
)

plt.title('Average Monthly Rolling Volatility by Year – Nifty 50 and Nifty 100', fontsize=16)
plt.xlabel('Month')
plt.ylabel('Year')
plt.tight_layout()
plt.show()

# Summary stats
vol_summary = daily_vol.groupby('index_name')['rolling_volatility'].agg(
    ['mean', 'min', 'max', 'std']
).round(2).rename(columns={
    'mean': 'Average Volatility (%)',
    'min': 'Lowest Volatility (%)',
    'max': 'Highest Volatility (%)',
    'std': 'Variability of Volatility'
})

print("\nVOLATILITY SUMMARY")
print(vol_summary)