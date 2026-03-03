# Combined box plot for NIFTY50, NIFTY100, NIFTY500 – closing prices and daily returns

import mysql.connector
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  
    'database': 'nifty100'
}

conn = mysql.connector.connect(**config)
print("Connected to MySQL.")

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

daily['trading_day'] = pd.to_datetime(daily['trading_day'], errors='coerce')
daily = daily.dropna(subset=['trading_day'])

print(f"Loaded {len(daily)} rows for all three indices.")


plt.figure(figsize=(10, 6))

sns.boxplot(
    data=daily,
    x='index_name',
    y='daily_close',
    palette='Set2',
    showmeans=True,
    meanprops={"marker":"D", "markerfacecolor":"black", "markeredgecolor":"black"}
)


counts = daily.groupby('index_name')['daily_close'].count()
for i, idx in enumerate(['NIFTY50', 'NIFTY100', 'NIFTY500']):
    max_val = daily[daily['index_name'] == idx]['daily_close'].max()
    plt.text(i, max_val * 1.02, f'n = {counts[idx]}', 
             ha='center', fontsize=10, color='black')

plt.title('Box Plot: Daily Closing Prices by Nifty Index', fontsize=14)
plt.xlabel('Index')
plt.ylabel('Closing Price')
plt.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.show()

print("Combined box plots for all three indices completed.")