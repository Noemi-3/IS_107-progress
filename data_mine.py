#Step-by-step Guide for Data Mining Tasks

#1. CUSTOMER SEGMENTATION USING CLUSTERING

## Step 1.1: Install required libraries
# Ensure you have scikit-learn, pandas, and matplotlib installed.
# Run this in your terminal or add it to your script:
# pip install scikit-learn pandas matplotlib

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Database connection configuration
DATABASE_TYPE = 'postgresql'
DBAPI = 'psycopg2'
HOST = 'localhost' 
USER = 'postgres'
PASSWORD = 'deuavecnous1'
DATABASE = 'retail_db'
PORT = '5432'

engine = create_engine(f'{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}')

# Step 1.2: Load the cleaned dataset
# Adjusted query to align with the database schema
query = """
SELECT c.customer_id, 
       SUM(f.total_amount) AS total_spent, 
       COUNT(f.invoice_no) AS frequency, 
       MAX(t.invoice_date) AS last_purchase
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY c.customer_id
"""
df = pd.read_sql(query, engine)

# Step 1.3: Preprocess the data
# Calculate recency by subtracting the most recent purchase date from today
df['recency'] = (pd.Timestamp('2024-12-13') - pd.to_datetime(df['last_purchase'])).dt.days

# Normalize the features for clustering
scaler = StandardScaler()
features = ['total_spent', 'frequency', 'recency']
df_scaled = scaler.fit_transform(df[features])

# Step 1.4: Apply K-Means clustering
kmeans = KMeans(n_clusters=4, random_state=42)
df['cluster'] = kmeans.fit_predict(df_scaled)

# Step 1.5: Visualize the clusters
plt.figure(figsize=(10, 6))
plt.scatter(df['total_spent'], df['frequency'], c=df['cluster'], cmap='viridis')
plt.title("Customer Segmentation")
plt.xlabel("Total Spent")
plt.ylabel("Frequency")
plt.colorbar(label='Cluster')
plt.show()

# Save the segmented data for analysis
df.to_csv('customer_segments.csv', index=False)


# 2. PREDICTIVE ANALYSIS USING LINEAR REGRESSION

## Step 2.1: Import libraries
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# Step 2.2: Prepare the data
# Adjusted query to align with the database schema
query = """
SELECT DATE_TRUNC('month', t.invoice_date) AS month, 
       SUM(f.total_amount) AS total_sales
FROM fact_sales f
JOIN dim_time t ON f.time_id = t.time_id
GROUP BY month
ORDER BY month
"""
sales_data = pd.read_sql(query, engine)

sales_data['month'] = pd.to_datetime(sales_data['month'])
sales_data['month_number'] = sales_data['month'].dt.strftime('%Y%m').astype(int)

X = sales_data[['month_number']]
y = sales_data['total_sales']

# Step 2.3: Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Step 2.4: Train the Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Step 2.5: Evaluate the model
predictions = model.predict(X_test)
print("RMSE:", mean_squared_error(y_test, predictions, squared=False))
print("R^2:", r2_score(y_test, predictions))

# Step 2.6: Forecast future sales
future_months = pd.DataFrame({'month_number': range(sales_data['month_number'].max() + 1, sales_data['month_number'].max() + 13)})
future_sales = model.predict(future_months)

# Plot actual vs predicted sales
plt.figure(figsize=(10, 6))
plt.plot(sales_data['month'], sales_data['total_sales'], label='Actual Sales')
plt.plot(pd.date_range(sales_data['month'].max(), periods=12, freq='M'), future_sales, label='Forecasted Sales', linestyle='--')
plt.title("Sales Forecast")
plt.xlabel("Month")
plt.ylabel("Total Sales")
plt.legend()
plt.show()

# Save forecast results
forecast_df = pd.DataFrame({
    'month': pd.date_range(sales_data['month'].max(), periods=12, freq='M'),
    'forecasted_sales': future_sales
})
forecast_df.to_csv('sales_forecast.csv', index=False)


# 3. INTEGRATING RESULTS INTO DASHBOARD

## Step 3.1: Add Clustering Results to Dashboard
# Update the PostgreSQL database with cluster assignments
for _, row in df.iterrows():
    cluster_update_query = f"""
    UPDATE dim_customer SET cluster = {row['cluster']} WHERE customer_id = {row['customer_id']};
    """
    engine.execute(cluster_update_query)

## Step 3.2: Add Sales Forecast Results to Dashboard
forecast_df.to_sql('sales_forecast', engine, if_exists='replace', index=False)

# Dashboard changes should dynamically pull clustering and forecast data for visualization.