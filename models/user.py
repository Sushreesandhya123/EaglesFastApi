import sys
sys.path.append("..")
from database import BASE
from .basic_import import *
from sqlalchemy import Column, BigInteger, String, Date, ForeignKey
from sqlalchemy.orm import relationship
class Users(BASE):
    __tablename__ = "tbl_users"
    user_id = Column(BigInteger,primary_key=True,autoincrement=True)
    org_id = Column(BigInteger,ForeignKey("tbl_organization.org_id",ondelete="SET NULL"))
    role = Column(String(255))
    user_name = Column(String(255))
    user_email= Column(String(255))
    user_mobile = Column(String(10))
    user_password = Column(String(255))
    user_dp = Column(String(255))
    timestamp = Column(DateTime)
    otp_hash  = Column(String(255))
    otp_expires = Column(DateTime)
    is_active = Column(Boolean,default=True)
    is_deleted = Column(Boolean,default=False)
    
    # relation
    organization = relationship("Organization", back_populates="users")

    
