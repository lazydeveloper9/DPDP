from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class KycRecord(Base):
    __tablename__ = "kyc_records"
    id = Column(Integer, primary_key=True)
    aadhaar_number = Column(String(12), nullable=False)
    pan_number = Column(String(10), nullable=False)
