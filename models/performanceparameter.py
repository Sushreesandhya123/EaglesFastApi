import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship

class PerformanceParameter(BASE):
    __tablename__ = "tbl_performanceparameter"
    parameter_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    min_rating = Column(Integer, nullable=False)
    max_rating = Column(Integer, nullable=False)
    