import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship

class SessionModel(BASE):
    __tablename__="tbl_session"
    session_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_name = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False)
    

    