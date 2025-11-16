# models.py
from sqlalchemy import Column, Integer, String, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Car(Base):
    __tablename__ = 'cars'
    
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

# Create engine
engine = create_engine('sqlite:///./db/cars.db')
Session = sessionmaker(bind=engine)
