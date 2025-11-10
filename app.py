import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from cost_calculator import generate_cost_series, depreciate_value, calculate_bijtelling

st.title("Interactive Car Cost Comparison Dashboard")
st.markdown("Fully configurable tool for comparing business lease, personal lease, and cash purchase scenarios over 5 years, with depreciation in cash TCO.")

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
    
    st.subheader("Operating Costs")
    fuel_cost_per_km = st.number_input("Fuel Cost per KM (€, petrol)", value=0.12)
    ev_cost_per_km = st.number_input("EV Cost per KM (€, electricity)", value=0.08)
    insurance_monthly_cash = st.number_input("Insurance Monthly (€, cash buy)", value=265)
    maintenance_yearly_cash = st.number_input("Maintenance Yearly (€, cash buy)", value=500)
    road_taxes_yearly_cash = st.number_input("Motorrijtuigenbelasting Yearly (€, cash buy)", value=850)
    
    st.subheader("Depreciation Model")
    decay_rate_new = st.number_input("Decay Rate New Cars (k, annual)", value=0.15)
    decay_rate_used = st.number_input("Decay Rate Used Cars (k, annual)", value=0.08)
    residual_percentage = st.number_input("Residual % of Purchase (floor)", value=0.20)

# Main Body: Car and Scenario Inputs
st.header("Scenario Configuration")
with st.expander("Car Details", expanded=True):
    selected_car = st.selectbox("Select Car", ["Tesla Model 3 LR"])
    purchase_price_new = st.number_input(f"New Purchase Price (€) for {selected_car}", value=40000)
    purchase_price_used = st.number_input("Used Purchase Price (€)", value=17000)
    is_used_cash = st.checkbox("Cash Buy is Used Car?", value=True)
    purchase_price = purchase_price_used if is_used_cash else purchase_price_new

with st.expander("Lease Details", expanded=True):
    cataloguswaarde = st.number_input("Cataloguswaarde (€) for Lease", value=40000)
    is_ev = st.checkbox("Is EV?", value=True)
    monthly_lease_business = st.number_input("Business Lease Monthly (€, company-paid; for ref)", value=500)
    monthly_lease_personal = st.number_input("Personal Lease Monthly (€, incl ins)", value=450)

if st.button("Generate Costs"):
    months, bus_costs, pers_costs, cash_costs = generate_cost_series(
        monthly_lease_business, monthly_lease_personal, purchase_price, is_used_cash, 
        cataloguswaarde, is_ev, years, km_per_year, fuel_cost_per_km, ev_cost_per_km,
        mobility_budget_gross_monthly, tax_rate_on_bijtelling, bijtelling_rate_ev_low, 
        bijtelling_rate_standard, insurance_monthly_cash, maintenance_yearly_cash,
        opportunity_rate, decay_rate_new, decay_rate_used, residual_percentage,
        road_taxes_yearly_cash
    )
    
    # Cumulative costs for line plots
    df = pd.DataFrame({
        'Month': months,
        'Business Lease': np.cumsum(bus_costs),
        'Personal Lease': np.cumsum(pers_costs),
        'Cash Purchase': np.cumsum(cash_costs)
    })
    
    # Interactive Plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Month'], y=df['Business Lease'], mode='lines', name='Business Lease'))
    fig.add_trace(go.Scatter(x=df['Month'], y=df['Personal Lease'], mode='lines', name='Personal Lease'))
    fig.add_trace(go.Scatter(x=df['Month'], y=df['Cash Purchase'], mode='lines', name='Cash Purchase (w/ Depr.)'))
    fig.update_layout(
        title=f"Cumulative Costs Over Time for {selected_car} (€)",
        xaxis_title="Months", yaxis_title="Cumulative Net Cost (TCO)",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Derived Insights
    annual_fuel_petrol = km_per_year * fuel_cost_per_km
    annual_fuel_ev = km_per_year * ev_cost_per_km
    st.info(f"Computed: Petrol Fuel €{annual_fuel_petrol:.0f}/year, EV Fuel €{annual_fuel_ev:.0f}/year")
    
    # Final residual for cash
    final_month = len(months)
    final_value, _ = depreciate_value(purchase_price, is_used_cash, final_month, decay_rate_new, decay_rate_used, residual_percentage)
    total_depr = purchase_price - final_value  # Net capital loss
    
    # Summary Table
    bus_total = df['Business Lease'].iloc[-1]
    pers_total = df['Personal Lease'].iloc[-1]
    cash_total = df['Cash Purchase'].iloc[-1]
    summary_data = {
        'Scenario': ['Business Lease (Total)', 'Personal Lease (Total)', 'Cash Purchase (Net TCO)'],
        'Monthly Avg (€)': [np.mean(bus_costs), np.mean(pers_costs), np.mean(cash_costs)],
        'Total Over Period (€)': [bus_total, pers_total, cash_total],
        'Key Component': [f'Net Bij + Mobility Loss', f'Lease + Fuel', f'Depr. {total_depr:.0f} + Ongoing']
    }
    summary = pd.DataFrame(summary_data)
    st.subheader("Cost Summary")
    st.table(summary)
    
    # Yearly Value Table
    st.subheader("Yearly Car Value (Exponential Decay)")
    years_list = list(range(1, years + 1))
    year_values = []
    annual_depr = []
    for y in years_list:
        month_end = y * 12
        value_end, _ = depreciate_value(purchase_price, is_used_cash, month_end, decay_rate_new, decay_rate_used, residual_percentage)
        year_values.append(value_end)
        value_start, _ = depreciate_value(purchase_price, is_used_cash, (y-1)*12 + 1, decay_rate_new, decay_rate_used, residual_percentage)
        annual_depr.append(value_start - value_end)
    depr_df = pd.DataFrame({
        'Year': years_list, 
        'Start Value (€)': [purchase_price if y==1 else year_values[y-2] for y in years_list],
        'End Value (€)': year_values,
        'Annual Depr. (€)': annual_depr
    })
    st.table(depr_df)

st.markdown("""
### Layout Insights
- **Sidebar Focus**: Limited to unchanging globals (e.g., tax_rate_on_bijtelling at 37% for NL brackets), enabling quick sensitivity tests without scrolling main—e.g., bump opportunity_rate to 7% and regenerate for inflation scenarios [web:16].
- **Main Efficiency**: Expanders group car/lease inputs (8 fields total), keeping the body airy; defaults to your €7k used EV budget for fast starts. Add more cars by editing the selectbox list [memory:12].
- **Workflow**: Set globals in sidebar first, then tweak scenarios in main, hit generate—plots/tables refresh instantly for iterative learning.
- **Extensions**: Use `st.columns` in main for side-by-side business/personal inputs if expanding to multi-scenario grids.
""")
