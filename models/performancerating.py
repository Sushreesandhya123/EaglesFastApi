from database import BASE
from sqlalchemy import Column, ForeignKey, Integer, String,BigInteger
from sqlalchemy.orm import relationship

class PerformanceRating(BASE):
    __tablename__ = "tbl_performance_rating"

    rating_id = Column(Integer, primary_key=True, autoincrement=True)
    emp_id = Column(BigInteger, ForeignKey('tbl_employee.emp_id'), nullable=False)
    parameter_id = Column(Integer, ForeignKey('tbl_performanceparameter.parameter_id'), nullable=False)
    session_id = Column(BigInteger, ForeignKey('tbl_session.session_id'), nullable=False)
    rating = Column(Integer, nullable=False)  # Rating value
    comments = Column(String(255)) # Optional comments

    # Relationships
    
    parameter = relationship("PerformanceParameter")
    session = relationship("SessionModel")
