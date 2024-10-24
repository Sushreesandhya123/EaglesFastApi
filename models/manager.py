import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship

class Manager(BASE):
    __tablename__="tbl_manager"
    manager_id = Column(Integer, primary_key=True, autoincrement=True)  
    manager_name = Column(String(100), nullable=False) 
    