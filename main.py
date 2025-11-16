from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import dash_daq as daq

from cost_calculator import simulate_costs_for_fleet

# Initialize app with Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define color scheme
COLORS = {
    'background': '#f8f9fa',
    'card': '#ffffff',
    'primary': '#0066cc',
    'secondary': '#6c757d',
    'text': '#212529'
}

# Custom styling for sliders
slider_style = {
    'padding': '20px 10px',
}

# App layout using Bootstrap components
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H2(
                "Vehicle Cost Comparison Dashboard",
                className="text-center mb-1 mt-4",
                style={'color': COLORS['text'], 'fontWeight': '600'}
            ),
            html.P(
                "Compare total costs over time for different scenarios",
                className="text-center text-muted mb-4",
                style={'fontSize': '14px'}
            )
        ], width=12)
    ]),
    
    # Main content card
    dbc.Card([
        dbc.CardBody([
            # Controls section
            dbc.Row([
                dbc.Col([
                    html.Label(
                        "Kilometers per Year",
                        style={'fontWeight': '500', 'marginBottom': '8px', 'fontSize': '14px'}
                    ),
                    dcc.Slider(
                        id="km-slider",
                        min=5_000,
                        max=40_000,
                        step=1_000,
                        value=15_000,
                        marks={k: f'{k//1000}k' for k in range(5_000, 40_001, 5_000)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], md=5, style=slider_style),
                
                dbc.Col([
                    html.Label(
                        "Number of Years",
                        style={'fontWeight': '500', 'marginBottom': '8px', 'fontSize': '14px'}
                    ),
                    dcc.Slider(
                        id="years-slider",
                        min=1,
                        max=10,
                        step=1,
                        value=4,
                        marks={y: str(y) for y in range(1, 11)},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], md=5, style=slider_style),

                dbc.Col([
                    html.Label("Display Mode", style={'fontWeight': '500', 'marginBottom': '8px', 'fontSize': '14px'}),
                    daq.ToggleSwitch(
                        id='cumulative-toggle',
                        value=True,
                        label={'label': 'Cumulative', 'style': {'fontSize': '14px'}},
                        labelPosition='bottom',
                        style={'marginTop': '10px'}
                    ),
                ], md=2, className="text-center"),
            ], className="mb-4"),
            
            # Graph section
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id="cost-graph",
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                        }
                    )
                ], width=12)
            ])
        ])
    ], className="shadow-sm", style={'border': 'none', 'borderRadius': '8px'}),
    
    # Summary cards row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Tesla Model 3", className="text-muted mb-2", style={'fontSize': '13px'}),
                    html.H4("—", id="tesla-total", style={'color': COLORS['primary'], 'fontWeight': '600'}),
                    html.P("Total Cost", className="text-muted mb-0", style={'fontSize': '12px'})
                ])
            ], className="text-center shadow-sm", style={'border': 'none', 'borderRadius': '8px'})
        ], md=6),
        
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Opel Corsa-e", className="text-muted mb-2", style={'fontSize': '13px'}),
                    html.H4("—", id="opel-total", style={'color': '#636EFA', 'fontWeight': '600'}),
                    html.P("Total Cost", className="text-muted mb-0", style={'fontSize': '12px'})
                ])
            ], className="text-center shadow-sm", style={'border': 'none', 'borderRadius': '8px'})
        ], md=6),
    ], className="mt-4 mb-4"),
    
], fluid=True, style={'backgroundColor': COLORS['background'], 'minHeight': '100vh', 'padding': '20px'})


@app.callback(
    [Output("cost-graph", "figure"),
     Output("tesla-total", "children"),
     Output("opel-total", "children"),
     Output("cumulative-toggle", "label")],
    [Input("km-slider", "value"),
     Input("years-slider", "value"),
     Input("cumulative-toggle", "value")]
)
def update_dashboard(n_kilometers_per_year, n_years, is_cumulative):
    # Vehicle data
    data = {
        "id": [1, 2], 
        "name": ["Tesla Model 3", "Opel Corsa-e"],  # Capitalized for display
        "type": ["buy", "buy"], 
        "build_year": [2019, 2022],
        "build_month": [1, 1],
        "buy_year": [2025, 2025],
        "buy_month": [11, 11],
        "purchase_cost": [18000.0, 17000.0],
        "road_taxes_yearly": [1000.0, 700.0],
        "insurance_monthly": [280.0, 180.0],
        "fuel_per_km": [0.08, 0.08],
        "depreciation_k": [0.08, 0.08]
    }
    df_pl = pl.DataFrame(data)
    
    # Calculate costs
    df_cost = simulate_costs_for_fleet(df_pl, n_years, n_kilometers_per_year)
    
    # Explode for plotting
    exploded_df = df_cost.with_columns(
        pl.int_ranges(1, pl.col("total_costs_over_time").list.len()+1).alias("month")
    ).explode(["total_costs_over_time", "month"])
    
    # Transform to monthly if needed (APP-SIDE)
    if not is_cumulative:
        exploded_df = exploded_df.with_columns([
            (pl.col("total_costs_over_time") - 
             pl.col("total_costs_over_time").shift(1).fill_null(0))
            .over("name")  # Group by vehicle name
            .alias("monthly_cost")
        ]).with_columns([
            pl.col("monthly_cost").alias("total_costs_over_time")
        ])
    
    # Update labels based on toggle
    y_label = "Total Cost (€)" if is_cumulative else "Monthly Cost (€)"
    toggle_label = "Cumulative" if is_cumulative else "Monthly"
    
    # Create plot (same as before, but dynamic y-axis label)
    fig = px.line(
        exploded_df,
        x="month",
        y="total_costs_over_time",
        color="name",
        labels={
            "total_costs_over_time": y_label, 
            "month": "Month",
            "name": "Vehicle"
        },
        color_discrete_map={
            "Tesla Model 3": "#0066cc",
            "Opel Corsa-e": "#636EFA"
        }
    )
    # Create modern-looking plot
    fig = px.line(
        exploded_df,
        x="month",
        y="total_costs_over_time",
        color="name",
        labels={
            "total_costs_over_time": y_label, 
            "month": "Month",
            "name": "Vehicle"
        },
        color_discrete_map={
            "Tesla Model 3": "#0066cc",
            "Opel Corsa-e": "#636EFA"
        }
    )
    
    # Update layout for modern look
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="system-ui, -apple-system, sans-serif", size=12, color=COLORS['text']),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#e0e0e0",
            borderwidth=1
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linewidth=1,
            linecolor='#e0e0e0'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linewidth=1,
            linecolor='#e0e0e0'
        )
    )
    
    # Update traces for smoother lines
    fig.update_traces(
        line=dict(width=3),
        hovertemplate='<b>%{fullData.name}</b><br>Month: %{x}<br>Cost: €%{y:,.0f}<extra></extra>'
    )
    
    # Get final costs (always from cumulative)
    final_costs = df_cost.select(["name", "total_costs_over_time"]).to_dicts()
    tesla_final = final_costs[0]["total_costs_over_time"][-1] if final_costs[0]["name"] == "Tesla Model 3" else final_costs[1]["total_costs_over_time"][-1]
    opel_final = final_costs[1]["total_costs_over_time"][-1] if final_costs[1]["name"] == "Opel Corsa-e" else final_costs[0]["total_costs_over_time"][-1]
    
    return (
        fig, 
        f"€{tesla_final:,.0f}", 
        f"€{opel_final:,.0f}",
        {'label': toggle_label, 'style': {'fontSize': '14px'}}
    )


if __name__ == "__main__":
    app.run(debug=True)
