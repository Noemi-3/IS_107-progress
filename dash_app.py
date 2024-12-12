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

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Function to load data from PostgreSQL
def load_data(query):
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of an error

# Dashboard layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Retail Sales Dashboard", className="text-center text-primary mb-2"), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.P("Explore sales trends, top-performing products, and geographical sales distribution.", 
                      className="text-center text-muted mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.H4("Date Range Picker", className="text-center text-secondary mb-2"), width=12),
        dbc.Col(
            dcc.DatePickerRange(
                id='date-picker',
                start_date='2010-12-01',
                end_date='2011-12-09',
                display_format='YYYY-MM-DD',
                className='mb-4 d-flex justify-content-center',
                style={'padding': '10px', 'textAlign': 'center'}
            ), width=6, className="mx-auto"
        )
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(dcc.Dropdown(id='product-dropdown', multi=True, placeholder="Select Products"), width=6),
        dbc.Col(dcc.Dropdown(id='country-dropdown', multi=True, placeholder="Select Countries"), width=6)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Total Sales", className="text-center text-dark"),
                html.P("This graph shows the total sales across the selected date range.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='total-sales-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top-Selling Products", className="text-center text-dark"),
                html.P("This bar chart highlights the top 10 products based on quantity sold.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='top-products-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=6),
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sales by Country", className="text-center text-dark"),
                html.P("This chart provides a breakdown of total sales by country.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='sales-by-country-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sales Trend Over Time", className="text-center text-dark"),
                html.P("This line chart shows how sales have varied over time within the selected range.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='sales-trend-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=12)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Product Sales Distribution", className="text-center text-dark"),
                html.P("This pie chart displays the distribution of sales among the top 10 products.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='product-sales-pie-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=12)
    ])
], fluid=True)


# Callback for dropdown filters
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
    LIMIT 10
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
        'data': [{
            'x': ['Total Sales'],
            'y': [total_sales['total_sales'][0]],
            'type': 'bar',
            'marker': {
                'color': 'rgba(0,123,255,0.8)'
            }
        }],
        'layout': {
            'title': 'Total Sales',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40}
        }
    }

    # Top Products Figure
    top_products_figure = {
        'data': [{
            'x': top_products['description'],
            'y': top_products['total_quantity'],
            'type': 'bar',
            'marker': {
                'color': [
                    'rgba(85,170,85,1)', 'rgba(76,153,76,1)', 'rgba(68,136,68,1)',
                    'rgba(59,119,59,1)', 'rgba(51,102,51,1)', 'rgba(42,85,42,1)',
                    'rgba(34,68,34,1)', 'rgba(25,51,25,1)', 'rgba(17,34,17,1)', 'rgba(8,17,8,1)'
                ]
            }
        }],
        'layout': {
            'title': 'Top Selling Products',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'hovermode': 'closest'
        }
    }

    # Sales by Country Figure
    sales_by_country_figure = {
        'data': [{
            'x': sales_by_country['country'],
            'y': sales_by_country['total_sales'],
            'type': 'bar',
            'marker': {
                'color': [
                    'rgba(255,102,102,1)', 'rgba(255,77,77,1)', 'rgba(255,51,51,1)',
                    'rgba(255,26,26,1)', 'rgba(255,0,0,1)', 'rgba(230,0,0,1)',
                    'rgba(204,0,0,1)', 'rgba(179,0,0,1)', 'rgba(153,0,0,1)', 'rgba(128,0,0,1)'
                ]
            }
        }],
        'layout': {
            'title': 'Sales by Country',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'hovermode': 'closest'
        }
    }

    # Sales Trend Figure
    sales_trend_figure = {
        'data': [{
            'x': sales_trend['invoice_date'],
            'y': sales_trend['total_sales'],
            'type': 'scatter',
            'mode': 'lines',
            'line': {
                'color': 'rgba(255,165,0,1)',
                'width': 2
            }
        }],
        'layout': {
            'title': 'Sales Trend Over Time',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40},
            'hovermode': 'closest'
        }
    }

    # Pie Chart Figure
    pie_figure = {
        'data': [{
            'labels': pie_data['description'],
            'values': pie_data['total_sales'],
            'type': 'pie',
            'hole': 0.4,
            'marker': {
                'colors': [
                    'rgba(255,99,132,1)', 'rgba(54,162,235,1)', 'rgba(255,206,86,1)',
                    'rgba(75,192,192,1)', 'rgba(153,102,255,1)', 'rgba(255,159,64,1)',
                    'rgba(255,107,107,1)', 'rgba(75,255,123,1)', 'rgba(255,119,255,1)', 'rgba(255,247,0,1)'
                ]
            }
        }],
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
