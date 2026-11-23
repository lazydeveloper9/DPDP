from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy_utils import EncryptedType

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    aadhaar_number = Column(EncryptedType(String(12)), nullable=False)
    pan_number = Column(EncryptedType(String(10)), nullable=False)
    email = Column(EncryptedType(String(255)), nullable=False)
