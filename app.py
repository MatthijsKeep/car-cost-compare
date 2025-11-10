import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from cost_calculator import generate_cost_series, depreciate_value, calculate_bijtelling
from config import CAR_MODELS, YEARS, MONTHS

st.title("Modular Car Cost Comparison Dashboard")
st.markdown("Interactive tool for comparing business lease, personal lease, and cash purchase scenarios over 5 years, with depreciation in cash TCO.")

# Sidebar Inputs
st.sidebar.header("Car Details")
selected_car = st.sidebar.selectbox("Select Car", CAR_MODELS)
purchase_price_new = st.sidebar.number_input(f"New Purchase Price (€) for {selected_car}", value=40000)
purchase_price_used = st.sidebar.number_input("Used Purchase Price (€)", value=17000)
cataloguswaarde = st.sidebar.number_input("Cataloguswaarde (€) for Lease", value=40000)
is_ev = st.sidebar.checkbox("Is EV?", value=True)
monthly_lease_business = st.sidebar.number_input("Business Lease Monthly (€, company-paid; for ref)", value=650)
monthly_lease_personal = st.sidebar.number_input("Personal Lease Monthly (€, incl ins)", value=650)
is_used_cash = st.sidebar.checkbox("Cash Buy is Used Car?", value=True)
tax_rate = st.sidebar.number_input("Your Marginal Tax Rate", value=0.37)

purchase_price = purchase_price_used if is_used_cash else purchase_price_new

if st.sidebar.button("Generate Costs"):
    months, bus_costs, pers_costs, cash_costs = generate_cost_series(
        monthly_lease_business, monthly_lease_personal, purchase_price, 
        is_used_cash, cataloguswaarde, is_ev
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
    
    # Final residual for cash
    final_value, _ = depreciate_value(purchase_price, is_used_cash, MONTHS)
    total_depr = purchase_price - final_value  # Net capital loss
    
    # Summary Table
    bus_total = df['Business Lease'].iloc[-1]
    pers_total = df['Personal Lease'].iloc[-1]
    cash_total = df['Cash Purchase'].iloc[-1]
    summary_data = {
        'Scenario': ['Business Lease (5y Total)', 'Personal Lease (5y Total)', 'Cash Purchase (5y Total, net TCO)'],
        'Monthly Avg (€)': [np.mean(bus_costs), np.mean(pers_costs), np.mean(cash_costs)],
        '5y Total (€)': [bus_total, pers_total, cash_total],
        'Key Component': [f'Net Bij + Mobility Loss', f'Lease + Fuel', f'Depr. {total_depr:.0f} + Ongoing']
    }
    summary = pd.DataFrame(summary_data)
    st.subheader("Cost Summary")
    st.table(summary)
    
    # Yearly Value Table (for depreciation insight)
    st.subheader("Yearly Car Value (Exponential Decay)")
    years_list = list(range(1, YEARS + 1))
    year_values = []
    annual_depr = []
    for y in years_list:
        month_end = y * 12
        value_end, _ = depreciate_value(purchase_price, is_used_cash, month_end)
        year_values.append(value_end)
        # Annual depr approx as difference
        value_start, _ = depreciate_value(purchase_price, is_used_cash, (y-1)*12 + 1)
        annual_depr.append(value_start - value_end)
    depr_df = pd.DataFrame({
        'Year': years_list, 
        'Start Value (€)': [purchase_price if y==1 else year_values[y-2] for y in years_list],
        'End Value (€)': year_values,
        'Annual Depr. (€)': [purchase_price * 0.15 if y==1 and not is_used_cash else d for y, d in zip(years_list, annual_depr)]  # Approx
    })
    st.table(depr_df)

st.markdown("""
### Model Insights
- **Depreciation Integration**: Monthly cash cost = ongoing + \( \frac{k}{12} v(t) \), where \( v(t) \) is mid-month value; total over 5 years ≈ net capital loss (purchase - residual ~€{purchase_price * 0.8 if new else 0.5}), plus operating/opportunity. For €7k used EV, expect ~€3.5k depreciation + €5k ongoing = €8.5k net TCO [memory:12].
- **Remaining Value**: Implicitly netted in total depreciation (residual not subtracted explicitly, as TCO reflects loss incurred). If selling, actual outflow = TCO - (realized residual - modeled residual); table shows projected €{purchase_price * 0.20 if used else 0.20} floor.
- **First Principles**: Exponential models front-load costs for new cars (higher early \( k \)), matching real afschrijving; opportunity at 6% approximates 4-5% savings rate + inflation. Bijtelling for €40k EV: €{calculate_bijtelling(40000, True)[0]:.0f} gross (~€{calculate_bijtelling(40000, True)[1]:.0f} net) [web:16].
- **Customizations**: Adjust \( k \) or residual % in `depreciate_value` for your BMW/Volvo/Tesla data; add inflation via `ongoing_monthly *= (1 + 0.02)**(month/12)`. For bundled fuel in personal lease, set to `monthly_lease` only [memory:6].
""")
