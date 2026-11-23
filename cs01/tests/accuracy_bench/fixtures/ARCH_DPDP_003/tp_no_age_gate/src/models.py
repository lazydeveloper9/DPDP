from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
