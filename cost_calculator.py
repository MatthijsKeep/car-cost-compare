import math

from config import (
    BIJTELLING_RATE_EV_LOW, BIJTELLING_RATE_STANDARD, TAX_RATE_ON_BIJTELLING, 
    YEARS, KM_PER_YEAR, FUEL_COST_PER_KM, MOBILITY_BUDGET_GROSS_MONTHLY,
    MAINTENANCE_YEARLY_CASH, INSURANCE_MONTHLY_CASH, MONTHS, EV_COST_PER_KM,
    ANNUAL_FUEL_EV, ANNUAL_FUEL_PETROL
)

def annual_fuel(is_ev):
    """Annual fuel cost based on EV status."""
    return ANNUAL_FUEL_EV if is_ev else ANNUAL_FUEL_PETROL

def calculate_bijtelling(cataloguswaarde, is_ev):
    """Annual bijtelling: gross and net after tax [web:16]."""
    if is_ev:
        low_part = min(cataloguswaarde, 30000) * BIJTELLING_RATE_EV_LOW
        high_part = max(0, cataloguswaarde - 30000) * BIJTELLING_RATE_STANDARD
    else:
        low_part, high_part = 0, cataloguswaarde * BIJTELLING_RATE_STANDARD
    annual_gross = low_part + high_part
    annual_net = annual_gross * TAX_RATE_ON_BIJTELLING  # Effective personal cost
    return annual_gross, annual_net

def depreciate_value(purchase_price, is_used, month):
    """Monthly depreciation using exponential decay: v(t) = p * e^{-k t}, steeper for new cars."""
    if is_used:
        k = 0.08  # Slower decay for used cars (~8% annual)
    else:
        k = 0.15  # Steeper for new (~15% annual, front-loaded)

    year = month / 12
    
    # Exponential value at year t
    value = purchase_price * math.exp(-k * year)
    
    # Floor at residual (20% of purchase)
    residual = purchase_price * 0.20
    value = max(value, residual)
    
    # Monthly depreciation: marginal loss for next month from current value
    monthly_factor = 1 - math.exp(-k / 12)
    monthly_depr = value * monthly_factor
    
    return value, monthly_depr

def business_lease_costs(monthly_lease, cataloguswaarde, is_ev):
    """Monthly business lease: lost mobility budget + net bijtelling"""
    annual_bij_gross, annual_bij_net = calculate_bijtelling(cataloguswaarde, is_ev)
    lost_mobility_annual_net = (MOBILITY_BUDGET_GROSS_MONTHLY * 12) * (1 - TAX_RATE_ON_BIJTELLING)  # Net value of lost benefit
    diff_budget = (monthly_lease - MOBILITY_BUDGET_GROSS_MONTHLY) * (1-TAX_RATE_ON_BIJTELLING) # if more than 650, cost extra, otherwise get money back
    total_annual = annual_bij_net + lost_mobility_annual_net + diff_budget
    return total_annual / 12

def personal_lease_costs(monthly_lease, is_ev):
    """Monthly personal lease: fixed, includes insurance, not fuel"""
    fuel_annual = annual_fuel(is_ev)
    return monthly_lease + (fuel_annual/12)

def cash_purchase_monthly_costs(purchase_price, is_used, month, is_ev):
    """Monthly cash buy: ongoing (fuel, ins, maint, opportunity) + depreciation (value loss)."""
    _, monthly_depr = depreciate_value(purchase_price, is_used, month)
    fuel_annual = annual_fuel(is_ev)
    maint_monthly = MAINTENANCE_YEARLY_CASH / 12
    ins_monthly = INSURANCE_MONTHLY_CASH
    opportunity_cost_yearly = purchase_price * 0.06
    ongoing_monthly = (fuel_annual / 12) + maint_monthly + ins_monthly + (opportunity_cost_yearly / 12)
    return ongoing_monthly + monthly_depr

def generate_cost_series(monthly_lease_business, monthly_lease_personal, purchase_price, is_used_cash, cataloguswaarde, is_ev):
    """Generate monthly cost arrays for all scenarios over projection period."""
    months = list(range(1, MONTHS + 1))
    
    # Constant scenarios
    bus_monthly = business_lease_costs(monthly_lease_business, cataloguswaarde, is_ev)
    bus_costs = [bus_monthly] * MONTHS
    pers_monthly = personal_lease_costs(monthly_lease_personal, is_ev=is_ev)
    pers_costs = [pers_monthly] * MONTHS
    
    # Monthly-varying cash with depreciation
    cash_costs = [cash_purchase_monthly_costs(purchase_price=purchase_price, is_used=is_used_cash, month=m, is_ev=is_ev) for m in months]
    
    return months, bus_costs, pers_costs, cash_costs