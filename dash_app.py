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

# Function to load data from PostgreSQL
def load_data(query):
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of an error

# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Dashboard layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Retail Sales Dashboard", className="text-center text-primary mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(html.P("Explore sales trends, top-performing products, and geographical sales distribution.", 
                      className="text-center text-muted mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Filters", className="text-center text-dark"),
                dbc.CardBody([
                    html.H5("Pick a Date Range", className="text-center text-secondary mb-3"),
                    dcc.DatePickerRange(
                        id='date-picker',
                        start_date='2010-12-01',
                        end_date='2011-12-09',
                        display_format='YYYY-MM-DD',
                        className='mb-4 d-flex justify-content-center',
                        style={'padding': '10px', 'textAlign': 'center'}
                    ),
                    html.H5("Pick a Country", className="text-center text-secondary mb-3"),
                    dcc.Dropdown(id='country-dropdown', multi=False, placeholder="Select Country", className='mb-4')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9', 'height': '300px'}), width=6
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Total Sales", className="text-center text-dark"),
                dbc.CardBody(
                    html.Div([
                        html.H2(id='total-sales-display', className="text-center text-success font-weight-bold", style={'fontSize': '3rem'}),
                        html.P("This section shows the total sales amount for the selected date range and country.", className="text-muted text-center")
                    ], className='d-flex flex-column justify-content-center align-items-center', style={'height': '100%'})
                )
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9', 'height': '300px'}), width=6
        )
    ], className="mb-4"),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Top-Selling Products", className="text-center text-dark"),
                html.P("This bar chart highlights the top 10 products based on quantity sold.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='top-products-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sales by Country", className="text-center text-dark"),
                html.P("This chart provides a breakdown of total sales by country.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='sales-by-country-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=6)
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Sales Trend Over Time", className="text-center text-dark"),
                html.P("This line chart shows how sales have varied over time within the selected range.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='sales-trend-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=6),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Product Sales Distribution", className="text-center text-dark"),
                html.P("This pie chart displays the distribution of sales among the top 10 products.", className="text-muted text-center mb-2"),
                dbc.CardBody([
                    dcc.Graph(id='product-sales-pie-chart')
                ])
            ], style={'boxShadow': '0 4px 8px rgba(0,0,0,0.2)', 'borderRadius': '10px', 'backgroundColor': '#f9f9f9'}), width=6)
    ])
], fluid=True)

# Callback for dropdown filters
@app.callback(
    Output('country-dropdown', 'options'),
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')]
)
def update_country_dropdown(start_date, end_date):
    country_options_query = f"""
    SELECT DISTINCT c.country AS label, c.country AS value
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    """
    country_options = load_data(country_options_query).to_dict('records')
    return country_options

# Callback for updating charts
@app.callback(
    [Output('total-sales-display', 'children'),
     Output('top-products-chart', 'figure'),
     Output('sales-by-country-chart', 'figure'),
     Output('sales-trend-chart', 'figure'),
     Output('product-sales-pie-chart', 'figure')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('country-dropdown', 'value')]
)
def update_charts(start_date, end_date, selected_country):
    country_filter = f"AND c.country = '{selected_country}'" if selected_country else ""

    # Query total sales
    total_sales_query = f"""
    SELECT SUM(total_amount) AS total_sales
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {country_filter}
    """
    total_sales = load_data(total_sales_query)

    total_sales_display = f"${total_sales['total_sales'][0]:,.2f}" if not total_sales.empty else "$0.00"

    # Query top-selling products (Top 10)
    top_products_query = f"""
    SELECT p.description, SUM(f.quantity) AS total_quantity
    FROM fact_sales f
    JOIN dim_product p ON f.product_id = p.product_id
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {country_filter}
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
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE t.invoice_date BETWEEN '{start_date}' AND '{end_date}'
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
    JOIN dim_customer c ON f.customer_id = c.customer_id
    WHERE f.time_id IN (
        SELECT time_id FROM dim_time
        WHERE invoice_date BETWEEN '{start_date}' AND '{end_date}'
    )
    {country_filter}
    GROUP BY p.description
    ORDER BY total_sales DESC
    LIMIT 10  -- Limit to top 10 for better visibility
    """
    pie_data = load_data(pie_chart_query)

    # Generate gradient colors for Top-Selling Products (Green shades)
    green_colors = [f'rgba(0,{200 - i*20},{0},1)' for i in range(len(top_products))]

    # Top Products Figure
    top_products_figure = {
        'data': [{
            'x': top_products['description'],
            'y': top_products['total_quantity'],
            'type': 'bar',
            'marker': {
                'color': green_colors
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

    # Generate gradient colors for Sales by Country (Red shades)
    red_colors = [f'rgba({255 - i*20},0,0,1)' for i in range(len(sales_by_country))]

    # Sales by Country Figure
    sales_by_country_figure = {
        'data': [{
            'x': sales_by_country['country'],
            'y': sales_by_country['total_sales'],
            'type': 'bar',
            'marker': {
                'color': red_colors
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
                    'rgba(75,192,192,1)', 'rgba(153,102,255,1)', 'rgba(255,159,64,1)'
                ]
            }
        }],
        'layout': {
            'title': 'Top Product Sales Distribution',
            'titlefont': {'size': 24},
            'height': 400,
            'margin': {'l': 40, 'r': 40, 't': 40, 'b': 40}
        }
    }

    return total_sales_display, top_products_figure, sales_by_country_figure, sales_trend_figure, pie_figure

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
