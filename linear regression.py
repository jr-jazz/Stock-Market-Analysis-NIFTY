import mysql.connector
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# === Connect to MySQL ===
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'nifty100'
}

conn = mysql.connector.connect(**config)
print("Connected successfully")

# loading tables
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

#linear regression and prediction model

# Convert trading_day to proper datetimeformat
daily['trading_day'] = pd.to_datetime(daily['trading_day'], errors='coerce')

# Drop any bad rows 
daily = daily.dropna(subset=['trading_day'])

print(f"Loaded {len(daily)} daily rows after date cleaning.")
print("Sample data:")
print(daily.head())
print("\nColumn types:")
print(daily.dtypes)

# Log transform (for percentage growth interpretation)
daily['log_close'] = np.log(daily['daily_close'])

# Linear regression for each index
results = []

for idx in daily['index_name'].unique():
    df_idx = daily[daily['index_name'] == idx].copy()
    
    df_idx['time_num'] = (df_idx['trading_day'] - df_idx['trading_day'].min()).dt.days
    
    X = df_idx['time_num'].values.reshape(-1, 1)
    y = df_idx['log_close'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    y_pred = model.predict(X)
    r2 = r2_score(y, y_pred)
    
    daily_growth_pct = model.coef_[0] * 100
    
    results.append({
        'Index': idx,
        'Slope (log)': round(model.coef_[0], 6),
        'Intercept': round(model.intercept_, 6),        
        'Approx Daily Growth %': round(daily_growth_pct, 4),
        'R²': round(r2, 4),
        'Start Date': df_idx['trading_day'].min().strftime('%Y-%m-%d'),
        'End Date': df_idx['trading_day'].max().strftime('%Y-%m-%d'),
        'Trading Days': len(df_idx)
    })

results_df = pd.DataFrame(results)
print(results_df)

# Show results
results_df = pd.DataFrame(results)
print("\n" + "="*70)
print("LINEAR REGRESSION RESULTS - LONG-TERM TREND (using daily tables)")
print("="*70)
print(results_df)
print("="*70)

# Predict future values for each index

future_days = [30, 90, 180, 365]  # 1 month, 3 months, 6 months, 1 year

predictions = []

for idx in daily['index_name'].unique():
    df_idx = daily[daily['index_name'] == idx].copy()
    df_idx['time_num'] = (df_idx['trading_day'] - df_idx['trading_day'].min()).dt.days
    
    row = results_df[results_df['Index'] == idx].iloc[0]
    slope = row['Slope (log)']
    start_date = df_idx['trading_day'].max()  # last real date
    last_log = np.log(df_idx['daily_close'].iloc[-1])  # last real log price
    
    for days in future_days:
        future_time_num = df_idx['time_num'].max() + days
        future_log = last_log + slope * days
        future_price = np.exp(future_log)
        
        predictions.append({
            'Index': idx,
            'Days Ahead': days,
            'Predicted Close': round(future_price, 2),
            'From Date': start_date.strftime('%Y-%m-%d'),
            'To Date': (start_date + pd.Timedelta(days=days)).strftime('%Y-%m-%d')
        })

pred_df = pd.DataFrame(predictions)
print("\n" + "="*60)
print("FUTURE PRICE PREDICTIONS (based on linear trend)")
print("="*60)
print(pred_df)
print("="*60)

# Save predictions back to MySQL

create_table_query = """
CREATE TABLE IF NOT EXISTS nifty_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    index_name VARCHAR(20) NOT NULL,
    days_ahead INT NOT NULL,
    predicted_close DECIMAL(12,2) NOT NULL,
    from_date DATE NOT NULL,
    to_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# Insert the predictions
insert_query = """
INSERT INTO nifty_predictions 
(index_name, days_ahead, predicted_close, from_date, to_date)
VALUES (%s, %s, %s, %s, %s)
"""

# Re-open connection to insert predictions
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Create table (safe to run multiple times)
cursor.execute(create_table_query)

# Insert each row
for _, row in pred_df.iterrows():
    cursor.execute(insert_query, (
        row['Index'],
        row['Days Ahead'],
        row['Predicted Close'],
        row['From Date'],
        row['To Date']
    ))

# Commit changes and close
conn.commit()
cursor.close()
conn.close()

print(f"Predictions saved to MySQL table 'nifty_predictions' ({len(pred_df)} rows)")

# Plot: actual prices + trend lines
plt.figure(figsize=(14, 8))
sns.lineplot(data=daily, x='trading_day', y='daily_close', hue='index_name', alpha=0.7)

# Vertical line at the end of real data
last_real_date = daily['trading_day'].max()
plt.axvline(
    x=last_real_date,
    color='black',
    linestyle='--',
    linewidth=1.5,
    label='End of Historical Data / Start of Prediction'
)

# Your existing trend lines loop
for idx in daily['index_name'].unique():
    df_idx = daily[daily['index_name'] == idx].copy()
    df_idx['time_num'] = (df_idx['trading_day'] - df_idx['trading_day'].min()).dt.days
    row = results_df[results_df['Index'] == idx].iloc[0]
    predicted_log = row['Intercept'] + row['Slope (log)'] * df_idx['time_num']
    predicted_price = np.exp(predicted_log)
    plt.plot(df_idx['trading_day'], predicted_price, linestyle='--', linewidth=2.5,
             label=f"{idx} Predicted Trend ({row['Approx Daily Growth %']:.4f}% daily)")

plt.title('Nifty Indices Daily Closing Prices with Fitted Linear Regression Trend Lines')
plt.xlabel('Date')
plt.ylabel('Closing Price')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()