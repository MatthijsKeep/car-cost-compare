# seed.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Car

# Create engine and session
engine = create_engine('sqlite:///./cars.db')
Session = sessionmaker(bind=engine)

def seed_cars():
    """Seed initial car data"""
    session = Session()
    
    # Check if data already exists (idempotency)
    if session.query(Car).count() > 0:
        print("Database already seeded, skipping...")
        session.close()
        return
    
    # Your seed data
    cars = [
        Car(
            name="tesla_model_3",
            type="buy",
            build_year=2019,
            build_month=1,
            buy_year=2025,
            buy_month=11,
            purchase_cost=18000.0,
            road_taxes_yearly=1000.0,
            insurance_monthly=280.0,
            fuel_per_km=0.08,
            depreciation_k=0.08
        ),
        Car(
            name="opel_corsa_e",
            type="buy",
            build_year=2022,
            build_month=1,
            buy_year=2025,
            buy_month=11,
            purchase_cost=17000.0,
            road_taxes_yearly=700.0,
            insurance_monthly=180.0,
            fuel_per_km=0.08,
            depreciation_k=0.08
        ),
    ]
    
    # Bulk insert for efficiency
    session.bulk_save_objects(cars)
    session.commit()
    print(f"Successfully seeded {len(cars)} cars")
    session.close()

if __name__ == "__main__":
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    # Seed data
    seed_cars()
