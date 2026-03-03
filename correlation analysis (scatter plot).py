# Correlation Analysis

import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'nifty100'
}

conn = mysql.connector.connect(**config)
print("Connected to MySQL successfully!")

# Load daily closing prices
query = """
SELECT 'NIFTY50' AS index_name, trading_day, avg_close AS daily_close
FROM nifty50_daily
UNION ALL
SELECT 'NIFTY100' AS index_name, trading_day, avg_close AS daily_close
FROM nifty100_daily
UNION ALL
SELECT 'NIFTY500' AS index_name, trading_day, avg_close AS daily_close
FROM nifty500_daily
ORDER BY index_name, trading_day
"""

daily = pd.read_sql(query, conn)
conn.close()

# Convert date to proper datetime
daily['trading_day'] = pd.to_datetime(daily['trading_day'], errors='coerce')
daily = daily.dropna(subset=['trading_day'])

print(f"Loaded {len(daily)} daily rows.")
print("Sample data:")
print(daily.head())

# Pivot data so each index is a separate column

pivot_close = daily.pivot(
    index='trading_day',
    columns='index_name',
    values='daily_close'
)

# Random sampling of 100 points for clearer scatter plot
# This creates a smaller dataset for clearer visualization
sample_close = pivot_close.sample(n=100, random_state=42) 

print(f"Sampled {len(sample_close)} random days for scatter plot.")

# Scatter plot with sampled data (much less congested)
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=sample_close,
    x='NIFTY50',
    y='NIFTY500',
    alpha=0.7,          
    s=60,         
    color='teal'
)

# Add regression line to the scatter plot
sns.regplot(
    data=sample_close,
    x='NIFTY50',
    y='NIFTY500',
    scatter=False, 
    color='red',
    line_kws={'linewidth': 2.5, 'linestyle': '--'}
)

plt.title('NIFTY50 vs NIFTY500 Daily Closes (Random Sample of 100 Days)', fontsize=14)
plt.xlabel('NIFTY50 Closing Price')
plt.ylabel('NIFTY500 Closing Price')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()