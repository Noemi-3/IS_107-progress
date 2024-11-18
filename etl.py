import pandas as pd
from sqlalchemy import create_engine, text

# Load online retail dataset
df = pd.read_excel(r'C:\Users\HP\Downloads\online+retail\Online_Retail.xlsx')

# Check the structure
print(df.info())
print(df.head())

# Remove rows with missing CustomerID and InvoiceNo
df_cleaned = df.dropna(subset=['CustomerID', 'InvoiceNo'])
print(df_cleaned.info()) # Check if rows with missing values are removed

# Remove duplicate rows
df_cleaned = df_cleaned.drop_duplicates()
print(df_cleaned.info()) # Confirm duplicates are removed

# Remove records with negative quantity or zero price
df_cleaned = df_cleaned[(df_cleaned['Quantity'] > 0) & (df_cleaned['UnitPrice'] > 0)]
print(df_cleaned.describe()) # Check if invalid rows are removed

# Create a 'TotalAmount' column
df_cleaned['TotalAmount'] = df_cleaned['Quantity'] * df_cleaned['UnitPrice']
print(df_cleaned.head()) # Verify that the new column has been created correctly

# Convert InvoiceDate to datetime
df_cleaned['InvoiceDate'] = pd.to_datetime(df_cleaned['InvoiceDate'])
print(df_cleaned.info()) # Ensure InvoiceDate is converted to datetime type

# Database connection
DATABASE_TYPE = 'postgresql'
DBAPI = 'psycopg2'
HOST = 'localhost'
USER = 'postgres'
PASSWORD = 'admin'
DATABASE = 'retail_db'
PORT = '5432'

engine = create_engine(f'{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}')
connection = engine.connect()

# Begin a transaction
transaction = connection.begin()

try:
    # ================== Populate dim_customer ==================
    customers = df_cleaned[['CustomerID', 'Country']].drop_duplicates()
    customers.columns = ['customer_id', 'country']

    for index, row in customers.iterrows():
        customer_id = int(row['customer_id'])  # Ensure it's an integer
        country = row['country'].replace("'", "''")  # Escape single quotes
        
        # Log every 100 rows only
        if index % 100 == 0:
            print(f"Inserting customer_id: {customer_id}, country: {country}")
        
        # SQL query to insert or update customer record
        sql_query = f"""
        INSERT INTO dim_customer (customer_id, country)
        VALUES ({customer_id}, '{country}')
        ON CONFLICT (customer_id) DO UPDATE
        SET country = '{country}';
        """
        
        connection.execute(text(sql_query))

    # ================== Populate dim_product ==================
    products = df_cleaned[['StockCode', 'Description', 'UnitPrice']].drop_duplicates()
    products.columns = ['product_id', 'description', 'unit_price']

    for index, row in products.iterrows():
        product_id = row['product_id']
        description = row['description'].replace("'", "''")  # Escape single quotes
        unit_price = row['unit_price']
        
        # Log every 100 rows only
        if index % 100 == 0:
            print(f"Inserting product_id: {product_id}, description: {description}, unit_price: {unit_price}")

        sql_query = f"""
        INSERT INTO dim_product (product_id, description, unit_price)
        VALUES ('{product_id}', '{description}', {unit_price})
        ON CONFLICT (product_id) DO UPDATE
        SET description = '{description}', unit_price = {unit_price};
        """
        
        connection.execute(text(sql_query))

    # ================== Populate dim_time ==================
    df_cleaned['InvoiceYear'] = df_cleaned['InvoiceDate'].dt.year
    df_cleaned['InvoiceMonth'] = df_cleaned['InvoiceDate'].dt.month
    time_dim = df_cleaned[['InvoiceDate', 'InvoiceMonth', 'InvoiceYear']].drop_duplicates()
    time_dim.columns = ['invoice_date', 'month', 'year']

    for index, row in time_dim.iterrows():
        invoice_date = row['invoice_date']
        month = row['month']
        year = row['year']
        
        # Log every 100 rows only
        if index % 100 == 0:
            print(f"Inserting invoice_date: {invoice_date}, month: {month}, year: {year}")

        sql_query = f"""
        INSERT INTO dim_time (invoice_date, month, year)
        VALUES ('{invoice_date}', {month}, {year})
        ON CONFLICT (invoice_date) DO UPDATE
        SET month = {month}, year = {year};
        """
        
        connection.execute(text(sql_query))

    # ================== Populate fact_sales ==================
    fact_sales_rows = []

    for index, row in df_cleaned.iterrows():
        invoice_no = row['InvoiceNo']
        customer_id = int(row['CustomerID'])
        product_id = row['StockCode']
        invoice_date = row['InvoiceDate']
        quantity = row['Quantity']
        total_amount = row['TotalAmount']

        # Get the time_id from dim_time based on invoice_date
        time_query = f"SELECT time_id FROM dim_time WHERE invoice_date = '{invoice_date}'"
        time_id = connection.execute(text(time_query)).fetchone()

        if not time_id:
            print(f"Time ID not found for invoice_date: {invoice_date}")
            continue

        # Check if customer and product exist in respective dimension tables
        customer_query = f"SELECT customer_id FROM dim_customer WHERE customer_id = {customer_id}"
        customer_result = connection.execute(text(customer_query)).fetchone()

        product_query = f"SELECT product_id FROM dim_product WHERE product_id = '{product_id}'"
        product_result = connection.execute(text(product_query)).fetchone()

        if not (customer_result and product_result):
            print(f"Customer or Product not found for: CustomerID {customer_id}, ProductID {product_id}")
            continue

        # Prepare the data for batch insert
        fact_sales_rows.append(
            f"('{invoice_no}', {customer_id}, '{product_id}', {time_id[0]}, {quantity}, {total_amount})"
        )

        # Insert in batches of 100 rows
        if len(fact_sales_rows) == 100:
            sql_query = f"""
            INSERT INTO fact_sales (invoice_no, customer_id, product_id, time_id, quantity, total_amount)
            VALUES {', '.join(fact_sales_rows)};
            """
            connection.execute(text(sql_query))
            print(f"Inserted batch of 100 rows into fact_sales")
            fact_sales_rows = []  # Clear the batch

    # Insert remaining rows if there are any left
    if fact_sales_rows:
        sql_query = f"""
        INSERT INTO fact_sales (invoice_no, customer_id, product_id, time_id, quantity, total_amount)
        VALUES {', '.join(fact_sales_rows)};
        """
        connection.execute(text(sql_query))
        print(f"Inserted final batch into fact_sales")

    # Commit the transaction
    transaction.commit()
    print("Data committed to the database successfully!")

except Exception as e:
    print(f"Error: {str(e)}")
    transaction.rollback()  # Rollback in case of an error

finally:
    connection.close()
    print("Connection closed.")
