import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input, Output
from sqlalchemy import create_engine

# Connect to PostgreSQL
DATABASE_TYPE = 'postgresql'
DBAPI = 'psycopg2'
HOST = 'localhost'  # Or your PostgreSQL host
USER = 'postgres'
PASSWORD = 'admin'
DATABASE = 'retail_db'
PORT = '5432'

engine = create_engine(f'{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}')

# Create Dash app with Bootstrap styling
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Function to load data from PostgreSQL
def load_data(query):
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of an error

# Layout of the dashboard
app.layout = dbc.Container([
    dbc.Row([ 
        dbc.Col(html.H1("Retail Sales Dashboard", className="text-center text-primary mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='product-dropdown', multi=True, placeholder="Select Products"), width=6),
        dbc.Col(dcc.Dropdown(id='country-dropdown', multi=True, placeholder="Select Countries"), width=6)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Total Sales", style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody(dcc.Graph(id='total-sales-chart'))
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px'}), width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top-Selling Products", style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody(dcc.Graph(id='top-products-chart'))
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px'}), width=6),
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sales by Country", style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody(dcc.Graph(id='sales-by-country-chart'))
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.Div("Select a Date Range"), className="text-center"),
        dbc.Col(dcc.DatePickerRange(
            id='date-picker',
            start_date='2010-12-01',
            end_date='2011-12-09',
            display_format='YYYY-MM-DD',
            style={'width': '100%', 'padding': '10px'}
        ), width=6),
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sales Trend Over Time", style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody(dcc.Graph(id='sales-trend-chart'))
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Product Sales Distribution", style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody(dcc.Graph(id='product-sales-pie-chart'))
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px'}), width=12)
    ])
], fluid=True)

# Callback for updating dropdown filters
@app.callback(
    [Output('product-dropdown', 'options'),
     Output('country-dropdown', 'options')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_dropdowns(start_date, end_date):
    # Query products for the dropdown
    product_options_query = f"""
    SELECT DISTINCT p.description AS label, p.product_id AS value
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    """
    product_options = load_data(product_options_query).to_dict('records')

    # Query countries for the dropdown
    country_options_query = f"""
    SELECT DISTINCT c.country AS label, c.customer_id AS value
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    """
    country_options = load_data(country_options_query).to_dict('records')

    return product_options, country_options

# Callback for updating charts
@app.callback(
    [Output('total-sales-chart', 'figure'),
     Output('top-products-chart', 'figure'),
     Output('sales-by-country-chart', 'figure'),
     Output('sales-trend-chart', 'figure'),
     Output('product-sales-pie-chart', 'figure')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('product-dropdown', 'value'),
     Input('country-dropdown', 'value')]
)
def update_charts(start_date, end_date, selected_products, selected_countries):
    # Modify queries to include product and country filters if selected
    product_filter = f"AND f.product_id IN {tuple(selected_products)}" if selected_products else ""
    country_filter = f"AND f.customer_id IN {tuple(selected_countries)}" if selected_countries else ""

    # Query total sales
    total_sales_query = f"""
    SELECT SUM(total_amount) AS total_sales
    FROM fact_sales f
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {product_filter}
    {country_filter}
    """
    total_sales = load_data(total_sales_query)

    # Query top-selling products (Top 10)
    top_products_query = f"""
    SELECT p.description, SUM(f.quantity) AS total_quantity
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {product_filter}
    GROUP BY p.description
    ORDER BY total_quantity DESC
    LIMIT 10  -- Expanded to top 10
    """
    top_products = load_data(top_products_query)

    # Query sales by country
    sales_by_country_query = f"""
    SELECT c.country, SUM(f.total_amount) AS total_sales
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {country_filter}
    GROUP BY c.country
    ORDER BY total_sales DESC
    """
    sales_by_country = load_data(sales_by_country_query)

    # Query sales trend by date
    sales_trend_query = f"""
    SELECT t.invoice_date, SUM(f.total_amount) AS total_sales
    FROM fact_sales f
    JOIN dim_time t ON f.time_id = t.time_id
    WHERE t.invoice_date BETWEEN '{start_date}' AND '{end_date}'
    {product_filter}
    {country_filter}
    GROUP BY t.invoice_date
    ORDER BY t.invoice_date
    """
    sales_trend = load_data(sales_trend_query)

    # Query sales distribution for the pie chart
    pie_chart_query = f"""
    SELECT p.description, SUM(f.total_amount) AS total_sales
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {product_filter}
    GROUP BY p.description
    ORDER BY total_sales DESC
    LIMIT 10  -- Limit to top 10 for better visibility
    """
    pie_data = load_data(pie_chart_query)

    # Total Sales Figure
    total_sales_figure = {
        'data': [{'x': ['Total Sales'], 'y': [total_sales['total_sales'][0]], 'type': 'bar', 'marker': {'color': '#007bff'}}],
        'layout': {
            'title': 'Total Sales',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40}
        }
    }

    # Top Products Figure
    top_products_figure = {
        'data': [{'x': top_products['description'], 'y': top_products['total_quantity'], 'type': 'bar', 'marker': {'color': '#28a745'}}],
        'layout': {
            'title': 'Top 10 Selling Products',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'hovermode': 'closest'  # Adding hover effects
        }
    }

    # Sales by Country Figure
    sales_by_country_figure = {
        'data': [{'x': sales_by_country['country'], 'y': sales_by_country['total_sales'], 'type': 'bar', 'marker': {'color': '#17a2b8'}}],
        'layout': {
            'title': 'Sales by Country',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'hovermode': 'closest'  # Adding hover effects
        }
    }

    # Sales Trend Figure
    sales_trend_figure = {
        'data': [{'x': sales_trend['invoice_date'], 'y': sales_trend['total_sales'], 'type': 'line', 'marker': {'color': '#dc3545'}}],
        'layout': {
            'title': 'Sales Trend Over Time',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'hovermode': 'closest'  # Adding hover effects
        }
    }

    # Pie Chart Figure
    pie_figure = {
        'data': [{'labels': pie_data['description'], 'values': pie_data['total_sales'], 'type': 'pie', 'hole': 0.4, 'marker': {
            'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF6B6B', '#4BFF7B', '#FF77FF', '#FFF700']
        }}],  # Donut style with custom colors
        'layout': {
            'title': 'Top Product Sales Distribution',
            'titlefont': {'size': 24},
            'showlegend': True,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'height': 400
        }
    }

    return total_sales_figure, top_products_figure, sales_by_country_figure, sales_trend_figure, pie_figure

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

