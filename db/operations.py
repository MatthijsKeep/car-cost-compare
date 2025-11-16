# db/operations.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from models import Car

import polars as pl

engine = create_engine('sqlite:///./db/cars.db')
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session():
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# CREATE
def create_car(car_data: dict) -> Car:
    """Add a new car to the database"""
    with get_session() as session:
        car = Car(**car_data)
        session.add(car)
        session.flush()  # Get the ID before committing
        return car

# READ
def get_car(car_id: int) -> Car | None:
    """Get a car by ID"""
    with get_session() as session:
        return session.query(Car).filter(Car.id == car_id).first()

def get_all_cars() -> list[Car]:
    """Get all cars"""
    with get_session() as session:
        return session.query(Car).all()

def search_cars(name: str = None, type: str = None) -> list[Car]:
    """Search cars with optional filters"""
    with get_session() as session:
        query = session.query(Car)
        if name:
            query = query.filter(Car.name.like(f'%{name}%'))
        if type:
            query = query.filter(Car.type == type)
        return query.all()

# UPDATE
def update_car(car_id: int, updates: dict) -> Car:
    """Update a car's fields"""
    with get_session() as session:
        car = session.query(Car).filter(Car.id == car_id).first()
        if not car:
            raise ValueError(f"Car {car_id} not found")
        
        for key, value in updates.items():
            setattr(car, key, value)
        
        session.flush()
        return car

# DELETE
def delete_car(car_id: int) -> bool:
    """Delete a car"""
    with get_session() as session:
        car = session.query(Car).filter(Car.id == car_id).first()
        if not car:
            return False
        session.delete(car)
        return True

# BULK OPERATIONS (for efficiency)
def bulk_create_cars(cars_data: list[dict]) -> None:
    """Efficiently create multiple cars"""
    with get_session() as session:
        session.bulk_insert_mappings(Car, cars_data)

if __name__ == "__main__":
    """
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String)
    build_year = Column(Integer)
    build_month = Column(Integer)
    buy_year = Column(Integer)
    buy_month = Column(Integer)
    purchase_cost = Column(Float)
    road_taxes_yearly = Column(Float)
    insurance_monthly = Column(Float)
    fuel_per_km = Column(Float)
    depreciation_k = Column(Float)
    """
    # Add a new car
    new_car = create_car({
        'name': 'bmw_3_series',
        'type': 'buy',
        'build_year': 2019,
        'build_month': 1,
        'buy_year': 2025,
        'buy_month': 1,
        'purchase_cost': 22000.0,
        'road_taxes_yearly': 800.0,
        'insurance_monthly': 180.0,
        'fuel_per_km': 0.11,
        'depreciation_k': 0.07,
    })

    delete_car(4)