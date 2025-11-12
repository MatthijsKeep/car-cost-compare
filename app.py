import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sqlite3
import math
import os

from cost_calculator import business_lease_costs, cash_purchase_monthly_costs, personal_lease_costs, depreciate_value

# Ensure DB file is in the app directory
DB_PATH = 'cars.db'

def init_db():
    """Initialize SQLite database with cars table and sample data."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            purchase_price_new REAL NOT NULL,
            purchase_price_used REAL,
            cataloguswaarde REAL NOT NULL,
            is_ev BOOLEAN DEFAULT 1,
            fuel_type TEXT DEFAULT 'ev' CHECK (fuel_type IN ('ev', 'petrol')),
            fuel_cost_per_km REAL DEFAULT 0.08,
            insurance_monthly_cash REAL DEFAULT 265,
            maintenance_yearly_cash REAL DEFAULT 500,
            road_taxes_yearly_cash REAL DEFAULT 850
        )
    ''')
    # Sample data for quick start (ignores if exists)
    sample_cars = [
        ('Tesla Model 3 LR', 50000, 17000, 51000, 1, 'ev', 0.08, 265, 500, 850),
        ('BMW 3 Series', 45000, 20000, 45000, 0, 'petrol', 0.12, 300, 600, 900),
        ('Volvo S60', 42000, 18000, 42000, 1, 'ev', 0.08, 280, 550, 800)
    ]
    c.executemany('''
        INSERT OR IGNORE INTO cars 
        (name, purchase_price_new, purchase_price_used, cataloguswaarde, is_ev, fuel_type, fuel_cost_per_km, insurance_monthly_cash, maintenance_yearly_cash, road_taxes_yearly_cash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_cars)
    conn.commit()
    conn.close()
    return True

# Initialize DB on app start
# init_db()

st.title("Interactive Car Cost Comparison Dashboard")
st.markdown("Fully configurable tool for comparing business lease, personal lease, and cash purchase scenarios over 5 years, with depreciation in cash TCO. Now with DB-backed multi-car scenarios.")

# Sidebar: Global Settings Only
with st.sidebar:
    st.header("Global Settings")
    
    st.subheader("Taxes & Rates")
    mobility_budget_gross_monthly = st.number_input("Mobility Budget Gross Monthly (€)", value=650)
    tax_rate_on_bijtelling = st.number_input("Marginal Tax Rate", value=0.37)
    bijtelling_rate_ev_low = st.number_input("Bijtelling EV Low Rate (up to €30k)", value=0.17)
    bijtelling_rate_standard = st.number_input("Bijtelling Standard Rate (above €30k/non-EV)", value=0.22)
    opportunity_rate = st.number_input("Opportunity Cost Rate (e.g., savings/inflation)", value=0.06)
    
    st.subheader("Usage & Projection")
    years = st.number_input("Projection Years", value=5, min_value=1, max_value=10)
    km_per_year = st.number_input("Annual KM Driven", value=15000)
    
    st.subheader("Operating Costs (Cash Defaults)")
    insurance_monthly_cash = st.number_input("Insurance Monthly (€, cash buy)", value=265)
    maintenance_yearly_cash = st.number_input("Maintenance Yearly (€, cash buy)", value=500)
    road_taxes_yearly_cash = st.number_input("Motorrijtuigenbelasting Yearly (€, cash buy)", value=850)
    
    st.subheader("Depreciation Model")
    decay_rate_new = st.number_input("Decay Rate New Cars (k, annual)", value=0.14)
    decay_rate_used = st.number_input("Decay Rate Used Cars (k, annual)", value=0.07)
    residual_percentage = st.number_input("Residual % of Purchase (floor)", value=0.20)

    # Admin Dashboard Toggle
    if st.checkbox("Admin Dashboard"):
        st.header("Admin: Manage Cars")
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql("SELECT * FROM cars", conn)
        conn.close()
        
        tab1, tab2, tab3 = st.tabs(["Add Car", "View/Edit", "Delete"])
        
        with tab1:
            st.header("Add New Car")
            name = st.text_input("Car Name")
            purchase_new = st.number_input("New Purchase Price (€)", value=40000.0, key="add_new")
            purchase_used = st.number_input("Used Purchase Price (€)", value=0.0, key="add_used")  # 0 for auto-compute if needed
            cataloguswaarde = st.number_input("Cataloguswaarde (€)", value=40000.0, key="add_cat")
            is_ev = st.checkbox("Is EV?", value=True, key="add_ev")
            fuel_type = st.selectbox("Fuel Type", ['ev', 'petrol'], key="add_fuel")
            fuel_cost_per_km = st.number_input("Fuel Cost per KM (€)", value=0.08 if is_ev else 0.12, key="add_fuel_cost")
            ins_monthly = st.number_input("Insurance Monthly Cash (€)", value=265, key="add_ins")
            maint_yearly = st.number_input("Maintenance Yearly Cash (€)", value=500, key="add_maint")
            taxes_yearly = st.number_input("Road Taxes Yearly Cash (€)", value=850, key="add_taxes")
            
            if st.button("Add Car"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute('''
                        INSERT INTO cars 
                        (name, purchase_price_new, purchase_price_used, cataloguswaarde, is_ev, fuel_type, fuel_cost_per_km, insurance_monthly_cash, maintenance_yearly_cash, road_taxes_yearly_cash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, purchase_new, purchase_used or purchase_new * 0.4, cataloguswaarde, is_ev, fuel_type, fuel_cost_per_km, ins_monthly, maint_yearly, taxes_yearly))
                    conn.commit()
                    st.success("Car added!")
                    st.rerun()  # Refresh to show updated data
                except Exception as e:
                    st.error(f"Error adding car: {e}")
                finally:
                    conn.close()
        
        with tab2:
            st.subheader("View & Edit Cars")
            st.dataframe(df)
            edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)
            if st.button("Save Edits"):
                conn = sqlite3.connect(DB_PATH)
                try:
                    edited_df.to_sql('cars', conn, if_exists='replace', index=False)
                    conn.commit()
                    st.success("Cars updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error updating: {e}")
                finally:
                    conn.close()
        
        with tab3:
            st.subheader("Delete Car")
            selected_name = st.selectbox("Select Car to Delete", df['name'].tolist() if not df.empty else [])
            if st.button("Delete Car"):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                try:
                    c.execute("DELETE FROM cars WHERE name=?", (selected_name,))
                    conn.commit()
                    st.success(f"{selected_name} deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting: {e}")
                finally:
                    conn.close()

# Load cars from DB for main app
def load_cars():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM cars", conn)
    conn.close()
    return df

cars_df = load_cars()

# Main Body: Multi-Scenario Configuration
st.header("Scenario Configuration")

if cars_df.empty:
    st.warning("No cars in database. Use Admin to add some.")
else:
    col1, col2, col3 = st.columns(3)
    scenarios = []
    
    with col1:
        st.subheader("Scenario 1")
        car1 = st.selectbox("Car", cars_df['name'].tolist(), key="car1")
        scenario1 = st.selectbox("Type", ["Business Lease", "Personal Lease", "Cash Buy"], key="scen1")
        scenarios.append((car1, scenario1))
    
    with col2:
        st.subheader("Scenario 2")
        car2 = st.selectbox("Car", ["None"] + cars_df['name'].tolist(), key="car2")
        scenario2 = st.selectbox("Type", ["None", "Business Lease", "Personal Lease", "Cash Buy"], key="scen2")
        if car2 != "None":
            scenarios.append((car2, scenario2))
    
    with col3:
        st.subheader("Scenario 3")
        car3 = st.selectbox("Car", ["None"] + cars_df['name'].tolist(), key="car3")
        scenario3 = st.selectbox("Type", ["None", "Business Lease", "Personal Lease", "Cash Buy"], key="scen3")
        if car3 != "None":
            scenarios.append((car3, scenario3))

    # Fetch car data for selected scenarios
    car_data = {}
    for car_name, scen in scenarios:
        if car_name in cars_df['name'].values:
            row = cars_df[cars_df['name'] == car_name].iloc[0]
            car_data[(car_name, scen)] = {
                'purchase_price_new': row['purchase_price_new'],
                'purchase_price_used': row['purchase_price_used'] or row['purchase_price_new'] * 0.4,
                'cataloguswaarde': row['cataloguswaarde'],
                'is_ev': row['is_ev'],
                'fuel_cost_per_km': row['fuel_cost_per_km'],
                'insurance_monthly_cash': row['insurance_monthly_cash'],
                'maintenance_yearly_cash': row['maintenance_yearly_cash'],
                'road_taxes_yearly_cash': row['road_taxes_yearly_cash']
            }

    # Lease inputs (per scenario, but default to car cataloguswaarde)
    lease_inputs = {}
    for car_name, scen in scenarios:
        if scen in ["Business Lease", "Personal Lease"]:
            with st.expander(f"Lease Details for {car_name} ({scen})", expanded=False):
                cat_val = car_data.get((car_name, scen), {}).get('cataloguswaarde', 40000)
                lease_inputs[(car_name, scen)] = {
                    'monthly_lease_business': st.number_input(f"Business Lease Monthly (€) for {car_name}", value=500, key=f"bus_{car_name}"),
                    'monthly_lease_personal': st.number_input(f"Personal Lease Monthly (€) for {car_name}", value=450, key=f"pers_{car_name}")
                }

if st.button("Generate Costs"):
    if not scenarios:
        st.warning("Select at least one scenario.")
    else:
        months = list(range(1, (years * 12) + 1))
        fig = go.Figure()
        all_costs = {}  # Dict for summary: scenario_name -> cumsum array
        
        for car_name, scen in scenarios:
            car_params = car_data[(car_name, scen)]
            is_used_cash = (scen == "Cash Buy")
            purchase_price = car_params['purchase_price_used'] if is_used_cash else car_params['purchase_price_new']
            is_ev = car_params['is_ev']
            fuel_cost_per_km = car_params['fuel_cost_per_km']
            ev_cost_per_km = fuel_cost_per_km if is_ev else 0.12  # Streamlined: use DB value for EV, fallback for petrol
            ins_monthly = car_params['insurance_monthly_cash']
            maint_yearly = car_params['maintenance_yearly_cash']
            taxes_yearly = car_params['road_taxes_yearly_cash']
            cat_val = car_params['cataloguswaarde']
            
            if scen == "Business Lease":
                bus_monthly = business_lease_costs(
                    lease_inputs[(car_name, scen)]['monthly_lease_business'], cat_val, is_ev,
                    mobility_budget_gross_monthly, tax_rate_on_bijtelling, bijtelling_rate_ev_low, bijtelling_rate_standard
                )
                bus_costs = [bus_monthly] * len(months)
                cumsum = np.cumsum(bus_costs)
                all_costs[f"{scen} {car_name}"] = cumsum
                fig.add_trace(go.Scatter(x=months, y=cumsum, mode='lines', name=f"{scen} {car_name}"))
            
            elif scen == "Personal Lease":
                pers_monthly = personal_lease_costs(
                    lease_inputs[(car_name, scen)]['monthly_lease_personal'], is_ev, km_per_year, fuel_cost_per_km, ev_cost_per_km
                )
                pers_costs = [pers_monthly] * len(months)
                cumsum = np.cumsum(pers_costs)
                all_costs[f"{scen} {car_name}"] = cumsum
                fig.add_trace(go.Scatter(x=months, y=cumsum, mode='lines', name=f"{scen} {car_name}"))
            
            elif scen == "Cash Buy":
                cash_costs = [cash_purchase_monthly_costs(
                    purchase_price, is_used_cash, m, is_ev, km_per_year, fuel_cost_per_km, ev_cost_per_km,
                    ins_monthly, maint_yearly, opportunity_rate, decay_rate_new, decay_rate_used, residual_percentage, taxes_yearly
                ) for m in months]
                cumsum = np.cumsum(cash_costs)
                all_costs[f"{scen} {car_name}"] = cumsum
                fig.add_trace(go.Scatter(x=months, y=cumsum, mode='lines', name=f"{scen} {car_name} (w/ Depr.)"))
        
        fig.update_layout(
            title=f"Cumulative Costs Over Time (€)",
            xaxis_title="Months", yaxis_title="Cumulative Net Cost (TCO)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Insights (use average fuel from scenarios)
        avg_fuel_ev = km_per_year * (ev_cost_per_km if any(is_ev for _, params in car_data.items() if params['is_ev']) else 0.08)
        avg_fuel_petrol = km_per_year * (fuel_cost_per_km if any(not params['is_ev'] for _, params in car_data.items()) else 0.12)
        st.info(f"Computed: Petrol Fuel €{avg_fuel_petrol:.0f}/year, EV Fuel €{avg_fuel_ev:.0f}/year")
        
        # Fixed Summary Table: Extract per-scenario totals and avgs
        if all_costs:
            totals = [cumsum[-1] for cumsum in all_costs.values()]
            monthly_avgs = [total / len(months) for total in totals]
            keys = list(all_costs.keys())
            key_components = [f'Net Bij + Mobility Loss' if 'Business' in k else f'Lease + Fuel' if 'Personal' in k else f'Depr. + Ongoing' for k in keys]
            
            summary_data = {
                'Scenario': keys,
                'Monthly Avg (€)': monthly_avgs,
                'Total Over Period (€)': totals,
                'Key Component': key_components
            }
            summary_df = pd.DataFrame(summary_data)
            st.subheader("Cost Summary")
            st.table(summary_df)
        
        # Yearly Depreciation for Cash Buys (aggregated if multiple)
        cash_scens = [(car, scen) for car, scen in scenarios if scen == "Cash Buy"]
        if cash_scens:
            st.subheader("Yearly Car Value (Exponential Decay)")
            years_list = list(range(1, years + 1))
            for car_name, _ in cash_scens:
                car_params = car_data[(car_name, "Cash Buy")]
                purchase_price = car_params['purchase_price_used']
                is_used = True
                year_values = []
                annual_depr = []
                for y in years_list:
                    month_end = y * 12
                    value_end, _ = depreciate_value(purchase_price, is_used, month_end, decay_rate_new, decay_rate_used, residual_percentage)
                    year_values.append(value_end)
                    value_start = purchase_price if y == 1 else year_values[y-2]
                    annual_depr.append(value_start - value_end)
                depr_df = pd.DataFrame({
                    'Year': years_list, 
                    'Start Value (€)': [purchase_price if y==1 else year_values[y-2] for y in years_list],
                    'End Value (€)': year_values,
                    'Annual Depr. (€)': annual_depr
                })
                st.subheader(f"Depreciation for {car_name}")
                st.table(depr_df)

st.markdown("""
### Usage Notes
- **DB Management**: Toggle Admin in sidebar to add/edit cars—data persists in `cars.db`.
- **Scenarios**: Select cars and types (e.g., Business Lease Tesla vs. Cash Buy BMW); lease details expand per scenario.
- **Efficiency**: Fuel costs pulled from DB; globals apply across. Regenerate for sensitivity tests.
- **Extensions**: Add more columns for scenarios if needed; `@st.cache_data` keeps queries fast.
""")
