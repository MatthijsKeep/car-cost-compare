def business_lease_costs(monthly_lease, cataloguswaarde, is_ev, mobility_budget_gross_monthly, tax_rate_on_bijtelling, bijtelling_rate_ev_low, bijtelling_rate_standard):
    """Monthly business lease: net bijtelling + lost mobility net + excess lease over budget (company-paid base)."""
    annual_bij_gross, annual_bij_net = calculate_bijtelling(cataloguswaarde, is_ev, bijtelling_rate_ev_low, bijtelling_rate_standard, tax_rate_on_bijtelling)
    bij_monthly_net = annual_bij_net / 12
    lost_mobility_annual_net = (mobility_budget_gross_monthly * 12) * (1 - tax_rate_on_bijtelling)
    lost_mobility_monthly_net = lost_mobility_annual_net / 12
    excess_lease_monthly = max(0, monthly_lease - mobility_budget_gross_monthly)  # Direct excess as per spec
    total_monthly = bij_monthly_net + lost_mobility_monthly_net + excess_lease_monthly
    return total_monthly

def personal_lease_costs(monthly_lease, is_ev, km_per_year, fuel_cost_per_km, ev_cost_per_km):
    """Monthly personal lease: fixed (includes insurance), plus fuel (not bundled)."""
    fuel_annual = annual_fuel(km_per_year, fuel_cost_per_km, ev_cost_per_km, is_ev)
    return monthly_lease + (fuel_annual / 12)

def cash_purchase_monthly_costs(purchase_price, is_used, month, is_ev, km_per_year, fuel_cost_per_km, ev_cost_per_km, insurance_monthly_cash, maintenance_yearly_cash, opportunity_rate, decay_rate_new, decay_rate_used, residual_percentage, road_taxes_yearly_cash):
    """Monthly cash buy: ongoing (fuel, ins, maint, opportunity) + depreciation (value loss)."""
    _, monthly_depr = depreciate_value(purchase_price, is_used, month, decay_rate_new, decay_rate_used, residual_percentage)
    fuel_annual = annual_fuel(km_per_year, fuel_cost_per_km, ev_cost_per_km, is_ev)
    maint_monthly = maintenance_yearly_cash / 12
    ins_monthly = insurance_monthly_cash
    opportunity_cost_yearly = purchase_price * opportunity_rate
    ongoing_monthly = (fuel_annual / 12) + maint_monthly + ins_monthly + (opportunity_cost_yearly / 12) + (road_taxes_yearly_cash / 12)
    return ongoing_monthly + monthly_depr

def generate_cost_series(monthly_lease_business, monthly_lease_personal, purchase_price, is_used_cash, cataloguswaarde, is_ev, years, km_per_year, fuel_cost_per_km, ev_cost_per_km, mobility_budget_gross_monthly, tax_rate_on_bijtelling, bijtelling_rate_ev_low, bijtelling_rate_standard, insurance_monthly_cash, maintenance_yearly_cash, opportunity_rate, decay_rate_new, decay_rate_used, residual_percentage, road_taxes_yearly_cash):
    """Generate monthly cost arrays for all scenarios over projection period."""
    months = list(range(1, (years * 12) + 1))
    
    # Constant scenarios
    bus_monthly = business_lease_costs(monthly_lease_business, cataloguswaarde, is_ev, mobility_budget_gross_monthly, tax_rate_on_bijtelling, bijtelling_rate_ev_low, bijtelling_rate_standard)
    bus_costs = [bus_monthly] * len(months)
    pers_monthly = personal_lease_costs(monthly_lease_personal, is_ev, km_per_year, fuel_cost_per_km, ev_cost_per_km)
    pers_costs = [pers_monthly] * len(months)
    
    # Monthly-varying cash with depreciation
    cash_costs = [cash_purchase_monthly_costs(purchase_price, is_used_cash, m, is_ev, km_per_year, fuel_cost_per_km, ev_cost_per_km, insurance_monthly_cash, maintenance_yearly_cash, opportunity_rate, decay_rate_new, decay_rate_used, residual_percentage, road_taxes_yearly_cash) for m in months]
    
    return months, bus_costs, pers_costs, cash_costs

def annual_fuel(km_per_year, fuel_cost_per_km, ev_cost_per_km, is_ev):
    """Annual fuel cost based on EV status and inputs."""
    base_cost = ev_cost_per_km if is_ev else fuel_cost_per_km
    return km_per_year * base_cost

def calculate_bijtelling(cataloguswaarde, is_ev, bijtelling_rate_ev_low, bijtelling_rate_standard, tax_rate_on_bijtelling):
    """Annual bijtelling: gross and net after tax [web:16]."""
    if is_ev:
        low_part = min(cataloguswaarde, 30000) * bijtelling_rate_ev_low
        high_part = max(0, cataloguswaarde - 30000) * bijtelling_rate_standard
    else:
        low_part, high_part = 0, cataloguswaarde * bijtelling_rate_standard
    annual_gross = low_part + high_part
    annual_net = annual_gross * tax_rate_on_bijtelling  # Effective personal cost
    return annual_gross, annual_net