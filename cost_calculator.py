import math
import numpy as np
import polars as pl

def depreciate_value(purchase_price, month, decay_rate, residual_percentage):
    """Value and monthly depreciation using exponential decay: \( v(t) = p e^{-k t} \), steeper for new cars."""
    k = decay_rate
    
    t = (month - 0.5) / 12.0  # Mid-month time for approximation
    value = purchase_price * math.exp(-k * t)
    
    # Floor at residual
    residual = purchase_price * residual_percentage
    value = max(value, residual)
    
    # Monthly depreciation: approximate rate during the month
    monthly_depr = (k / 12.0) * value
    
    return value, monthly_depr

def cost_over_time(row: dict, n_years: int, n_kilometer_per_year: int) -> np.ndarray:
    n_months = n_years * 12
    costs = np.zeros(n_months)

    monthly_costs = (row["road_taxes_yearly"] / 12) + row["insurance_monthly"] + (n_kilometer_per_year / 12 * row["fuel_per_km"])

    for i in range(n_months):
        car_age_months = (row["buy_year"] * 12 + row["buy_month"] + i + 1) - (row["build_year"] * 12 + row["build_month"])
        if (row["type"] == "buy") and i == 0:
            costs[i] += row["purchase_cost"]
        if i >= 1:
            costs[i] += costs[i-1]
        remaining_value, depreciation_monthly = depreciate_value(purchase_price=row["purchase_cost"], month=car_age_months, decay_rate=row["depreciation_k"], residual_percentage=0.2)
        costs[i] += (monthly_costs + depreciation_monthly)
        if i == (n_months - 1):
            costs[i] -= remaining_value
        costs[i] = np.round(costs[i], decimals=2)

    return costs

def simulate_costs_for_fleet(
    df: pl.DataFrame, n_years: int, n_kilometer_per_year: int
) -> pl.DataFrame:
    rows_out = []

    for row in df.iter_rows(named=True):  # row is dict-like [web:14]
        car_costs = cost_over_time(row, n_years, n_kilometer_per_year)

        rows_out.append(
            {
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "build_year_month": str(row["build_year"]) + str(row["build_month"]),
                "n_years": n_years,
                "n_kilometer_per_year": n_kilometer_per_year,
                "total_costs_over_time": car_costs.tolist(),  # List[float] column [web:56]
                "final_cost": float(car_costs[-1]),
            }
        )

    # convert list-of-dicts to DataFrame
    result_df = pl.from_dicts(rows_out)  # one row per car, list column for time series [web:39]
    return result_df