import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship,joinedload 

class Project(BASE):
    __tablename__="tbl_project"
    project_id = Column(Integer, primary_key=True, autoincrement=True)  
    project_name = Column(String(100), nullable=False) 
    department_id = Column(Integer, ForeignKey('tbl_department.department_id',ondelete="CASCADE"),nullable=False)
    
    department = relationship("Department", back_populates="projects")  # Ensure you define this relationship if needed
    employees = relationship("Employee", back_populates="project")