from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuditLog(Base):
    """retention: 365 days per DPDP Rule 8"""
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), nullable=False)  # retention: 180 days
    action = Column(String(100))
