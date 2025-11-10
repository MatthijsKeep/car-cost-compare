# Dutch 2025 tax and cost parameters [web:16][web:22]
MOBILITY_BUDGET_GROSS_MONTHLY = 650  # € if no business lease [memory:5]

BIJTELLING_RATE_EV_LOW = 0.17  # Up to €30,000 for EVs
BIJTELLING_RATE_STANDARD = 0.22  # Above €30k or non-EV

TAX_RATE_ON_BIJTELLING = 0.37  # Placeholder marginal rate; adjust to yours

YEARS = 5  # Projection period
MONTHS = YEARS * 12
KM_PER_YEAR = 15000  # Annual km; impacts variable costs

FUEL_COST_PER_KM = 0.12  # €/km for cash buy (business lease include fuel)
EV_COST_PER_KM = 0.08 # €/km for cash buy (EV)

# Fuel costs: Leases include; cash differentiates EV vs. petrol
ANNUAL_FUEL_PETROL = KM_PER_YEAR * FUEL_COST_PER_KM  # €/year at €0.10/km
ANNUAL_FUEL_EV = KM_PER_YEAR * EV_COST_PER_KM  # €/year at €0.05/km electricity

INSURANCE_MONTHLY_CASH = 265  # € for cash purchase
MAINTENANCE_YEARLY_CASH = 400  # € annual for cash buy

CAR_MODELS = ["Tesla Model 3 LR"]

