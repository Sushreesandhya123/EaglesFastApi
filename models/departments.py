import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship

class Department(BASE):
    __tablename__="tbl_department"
    department_id = Column(Integer, primary_key=True, autoincrement=True)  
    department_name = Column(String(100), nullable=False) 

    employees = relationship("Employee", back_populates="department", cascade="all, delete")
    projects = relationship("Project", back_populates="department", cascade="all, delete")