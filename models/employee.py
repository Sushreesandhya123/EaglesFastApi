import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship
 
class Employee(BASE):
    __tablename__ = "tbl_employee"
 
    emp_id = Column(BigInteger, primary_key=True, autoincrement=True)
    employee_id = Column(String(50), nullable=False, unique=True)  # New field
    employee_name = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)  # Role can be 'Member', 'Manager', 'HR Admin'
     # Add manager_name column
    manager_name = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey('tbl_department.department_id', ondelete="CASCADE"), nullable=True)
    project_id = Column(Integer, ForeignKey('tbl_project.project_id', ondelete="CASCADE"), nullable=True)
 
    # Relationships
    department = relationship("Department", back_populates="employees")
    project = relationship("Project", back_populates="employees")
    