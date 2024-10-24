import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Text, Enum as SQLAlchemyEnum  # Import SQLAlchemy's Enum
from sqlalchemy.orm import relationship


class Organization(BASE):
    __tablename__ = "tbl_organization"
    org_id = Column(BigInteger, primary_key=True, autoincrement=True)
    org_name = Column(String(1000), nullable=False)
    org_email = Column(String(255), unique=True, nullable=False)   
    org_mobile_number = Column(String(15), nullable=False) 
    org_address = Column(Text)
    org_pincode = Column(String(20))
    org_city = Column(String(20))
    org_state = Column(String(20))
    org_country = Column(String(20))
    org_logo = Column(String(500))
    password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)  

    