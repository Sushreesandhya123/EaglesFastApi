from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship

class SessionEntryModal(BASE):
    __tablename__ = "tbl_sessionentry"
    sessionentry_id = Column(Integer, primary_key=True, autoincrement=True)  
    session_id = Column(BigInteger, ForeignKey('tbl_session.session_id', ondelete="CASCADE"), nullable=True)  # Change to BigInteger
    emp_id = Column(BigInteger, ForeignKey('tbl_employee.emp_id', ondelete="CASCADE"), nullable=True)
    org_id = Column(BigInteger, ForeignKey('tbl_organization.org_id', ondelete="CASCADE"), nullable=True)
    parameter_id = Column(Integer, ForeignKey('tbl_performanceparameter.parameter_id', ondelete="CASCADE"), nullable=True)
    rating = Column(Integer, nullable=False)  
    comments = Column(String(255), nullable=True)  