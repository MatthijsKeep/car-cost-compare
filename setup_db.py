import sqlite3

def init_db():
    conn = sqlite3.connect('cars.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            purchase_price_new REAL NOT NULL,
            purchase_price_used REAL,  -- Optional; compute as ~0.4 * new if null
            cataloguswaarde REAL NOT NULL,
            is_ev BOOLEAN DEFAULT 1,
            fuel_type TEXT DEFAULT 'ev' CHECK (fuel_type IN ('ev', 'petrol')),  -- Drives cost_per_km
            fuel_cost_per_km REAL DEFAULT 0.08,  -- Auto-set based on fuel_type
            insurance_monthly_cash REAL DEFAULT 265,
            maintenance_yearly_cash REAL DEFAULT 500,
            road_taxes_yearly_cash REAL DEFAULT 850
        )
    ''')
    # Sample data for quick start
    sample_cars = [
        ('Tesla Model 3 LR', 47000, 17000, 51000, 1, 'ev',      0.08, 265, 500, 850),
        ('BMW 3 Series',    45000,  20000, 45000, 0, 'petrol',  0.12, 150, 800, 800)
    ]
    c.executemany('''
        INSERT OR IGNORE INTO cars 
        (name, purchase_price_new, purchase_price_used, cataloguswaarde, is_ev, fuel_type, fuel_cost_per_km, insurance_monthly_cash, maintenance_yearly_cash, road_taxes_yearly_cash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_cars)
    conn.commit()
    conn.close()
