from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    aadhaar_number = Column(String(12), nullable=False)
    pan_number = Column(String(10), nullable=False)
    email = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
