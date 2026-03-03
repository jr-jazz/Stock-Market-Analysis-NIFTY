# NIFTY50: price trend + volatility prediction

import mysql.connector
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt

# Connect to MySQL and load daily data
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # CHANGE THIS
    'database': 'nifty100'
}

conn = mysql.connector.connect(**config)
print("Connected to MySQL.")

query = """
SELECT trading_day, avg_close AS daily_close
FROM nifty50_daily
ORDER BY trading_day
"""

daily = pd.read_sql(query, conn)
cursor=conn.close()

daily['trading_day'] = pd.to_datetime(daily['trading_day'], errors='coerce')
daily = daily.dropna(subset=['trading_day'])

print(f"Loaded {len(daily)} NIFTY50 daily rows.")

# Calculate daily returns and rolling volatility (standard deviation of returns)
daily['daily_return'] = daily['daily_close'].pct_change() * 100

window = 30
daily['rolling_volatility'] = daily['daily_return'].rolling(window=window, min_periods=1).std()

daily_vol = daily.dropna(subset=['rolling_volatility'])

print(f"Volatility calculated ({len(daily_vol)} rows after dropna).")

# Train linear regression for PRICE trend (log close vs time)
df_price = daily.copy()
df_price['time_num'] = (df_price['trading_day'] - df_price['trading_day'].min()).dt.days
df_price['log_close'] = np.log(df_price['daily_close'])

X_price = df_price['time_num'].values.reshape(-1, 1)    # This is X for price model
y_price = df_price['log_close'].values                  # This is y for price model

model_price = LinearRegression()
model_price.fit(X_price, y_price)

y_pred_price = model_price.predict(X_price)
r2_price = r2_score(y_price, y_pred_price)

price_slope = model_price.coef_[0]
price_intercept = model_price.intercept_
price_growth_pct = price_slope * 100

print("\nPrice Trend Model (NIFTY50):")
print(f"Slope (log): {price_slope:.6f}")
print(f"Intercept: {price_intercept:.4f}")
print(f"Approx Daily Growth %: {price_growth_pct:.4f}")
print(f"R²: {r2_price:.4f}")

#Train linear regression for VOLATILITY trend (vol vs time)
df_vol = daily_vol.copy()
df_vol['time_num'] = (df_vol['trading_day'] - df_vol['trading_day'].min()).dt.days

X_vol = df_vol['time_num'].values.reshape(-1, 1)  # This is X for volatility model
y_vol = df_vol['rolling_volatility'].values       # This is y for volatility model

model_vol = LinearRegression()
model_vol.fit(X_vol, y_vol)

y_pred_vol = model_vol.predict(X_vol)
r2_vol = r2_score(y_vol, y_pred_vol)

vol_slope = model_vol.coef_[0]
vol_intercept = model_vol.intercept_

print("\nVolatility Trend Model (NIFTY50):")
print(f"Slope: {vol_slope:.6f}")
print(f"Intercept: {vol_intercept:.4f}")
print(f"R²: {r2_vol:.4f}")

# ask for input on how many days ahead to predict (default 365 if invalid input)
print("\n--- Prediction Request (NIFTY50 only) ---")
try:
    days_ahead = int(input("How many days ahead to predict? (e.g. 30, 90, 365): "))
    if days_ahead <= 0:
        raise ValueError
except:
    print("Invalid input. Using 365 days.")
    days_ahead = 365

print(f"Predicting {days_ahead} days ahead for NIFTY50.")


# Generate predictions for both price and volatility

pred_rows = []

# Last known values for NIFTY50
last_time_price = df_price['time_num'].max()
last_date = df_price['trading_day'].max()
last_price = df_price['daily_close'].iloc[-1]

last_time_vol = df_vol['time_num'].max()
last_vol = df_vol['rolling_volatility'].iloc[-1]

# Future time steps
future_time_price = np.arange(last_time_price + 1, last_time_price + days_ahead + 1)
future_time_vol = np.arange(last_time_vol + 1, last_time_vol + days_ahead + 1)

# Predict price using the linear model (log scale)
future_log_price = price_intercept + price_slope * future_time_price
future_price = np.exp(future_log_price)

# Predict volatility
future_vol = vol_intercept + vol_slope * future_time_vol

# Future dates
future_dates = pd.date_range(
    start=last_date + pd.Timedelta(days=1),
    periods=days_ahead,
    freq='B'  # business days
)

# Build rows for DataFrame
for i in range(days_ahead):
    future_date = future_dates[i].date()
    pred_rows.append({
        'future_date': future_date,
        'predicted_price': round(future_price[i], 2),
        'predicted_volatility': round(future_vol[i], 4)
    })

pred_df = pd.DataFrame(pred_rows)

# Print sample
print(f"\nGenerated {len(pred_df)} predictions for NIFTY50 ({days_ahead} days ahead).")
print("First 8 rows:")
print(pred_df.head(8))
print("\nLast 4 rows:")
print(pred_df.tail(4))

# Save to MySQL
conn = mysql.connector.connect(**config)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS nifty50_predictions_price_volatility (
    id INT AUTO_INCREMENT PRIMARY KEY,
    future_date DATE NOT NULL,
    predicted_price DECIMAL(12,2) NOT NULL,
    predicted_volatility DECIMAL(10,4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

insert_query = """
INSERT INTO nifty50_predictions_price_volatility
(future_date, predicted_price, predicted_volatility)
VALUES (%s, %s, %s)
"""

values = [
    (row['future_date'], row['predicted_price'], row['predicted_volatility'])
    for _, row in pred_df.iterrows()
]

cursor.executemany(insert_query, values)
conn.commit()

cursor.close()
conn.close()

print(f"Saved {len(values)} rows to table 'nifty50_predictions_price_volatility'.")


# Plot: Combined Price Trend + Volatility (historical + prediction)
fig, ax1 = plt.subplots(figsize=(14, 7))

# Left axis: Volatility
ax1.set_xlabel('Date')
ax1.set_ylabel(f'{window}-Day Rolling Volatility (%)', color='tab:blue')
ax1.tick_params(axis='y', labelcolor='tab:blue')

ax1.plot(daily_vol['trading_day'], daily_vol['rolling_volatility'],
         color='tab:blue', linewidth=2, label='Historical Volatility')

ax1.plot(future_dates, future_vol,
         color='tab:blue', linestyle=':', linewidth=2.5, label=f'Predicted Volatility ({days_ahead} days)')

# Vertical separator
ax1.axvline(x=last_date, color='black', linestyle='--', linewidth=1.5,
            label='End of Historical Data')

# Right axis: Price Trend
ax2 = ax1.twinx()
ax2.set_ylabel('Closing Price', color='tab:orange')
ax2.tick_params(axis='y', labelcolor='tab:orange')

ax2.plot(df_price['trading_day'], df_price['daily_close'],
         color='tab:orange', linewidth=1.5, alpha=0.7, label='Historical Close')

ax2.plot(future_dates, future_price,
         color='tab:orange', linestyle='--', linewidth=2.5, label=f'Predicted Price Trend ({days_ahead} days)')

# Titles & legend
fig.suptitle('NIFTY50: Closing Price Trend + Rolling Volatility + Prediction', fontsize=16)
fig.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
ax1.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()


