from typing import Optional
from fastapi import routing,status
from fastapi.routing import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel,Field
from fastapi.encoders import jsonable_encoder
from .users.login import get_current_user
from datetime import datetime
from enum import Enum
from fastapi import APIRouter,status,Depends
from pytz import timezone
router=APIRouter()

def send_message(msg,data=None):
    return {"status_code":200,"msg":msg,"response":data}

def raise_exception(status_code:int=None,detail:str=None):
    raise HTTPException(status_code=status_code,detail=detail)


async def check_instance(model=None,field_name:str=None,field_value=None,db=None):
    try:
        instance = db.query(model).filter(getattr(model, field_name) == field_value,model.is_deleted==False).first()
    except Exception as e:
        instance = db.query(model).filter(getattr(model, field_name) == field_value).first()
    if instance is not None:
        return instance
    return None


def succes_response(data=None,msg=None):
    return {"status_code":200,"msg":msg,"response":jsonable_encoder(data)}


async def get_current_ist_time():
    ist_timezone = timezone("Asia/Kolkata")
    current_time = datetime.now(ist_timezone)
    return current_time

class Role(str, Enum):
    member = "Member"
    manager = "Manager"
    hr_admin = "HR Admin"

def is_authenticated(*allowed_roles):
    def wrapper(current_user = Depends(get_current_user)):
        target_outlet_id = 0
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

        if allowed_roles[0] != "*" and current_user.role.capitalize() not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action!")

 