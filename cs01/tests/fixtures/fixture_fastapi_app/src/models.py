from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    # Violation: Unencrypted Aadhaar column (SQL-DPDP-001)
    aadhaar_number = Column(String(12), nullable=False)
    # Violation: Date of birth collected without guardian gate (ARCH-DPDP-003)
    date_of_birth = Column(Date, nullable=False)
