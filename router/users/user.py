from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import bcrypt
from enum import Enum
from router.basic_import import *
from database import engine, connect_db, db_dependency  # Ensure this is defined in `database.py`
from models.user import Users
from models.organization import Organization
from .login import get_password_hash, oauth2_scheme,get_current_user
from datetime import datetime
from fastapi.encoders import jsonable_encoder
 
# Users.metadata.create_all(bind=engine)
router = APIRouter()
 
class Role(str, Enum):
    member = "Member"
    manager = "Manager"
    hr_admin = "HR Admin"
 
 
class UserBase(BaseModel):
    org_id: int
    role: Role = Role.hr_admin
    user_name: str = Field(default="Rupashree")
    user_email: EmailStr = Field(default="rupashree@gmail.com")
    user_mobile: str = Field(min_length=10, max_length=10, default="90100***07")
    user_password: str
    user_dp: str
 
class UserCreate(UserBase):
    user_password: str  # Required field for creation
    org_id: int  # Ensure this field is present
 
class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_mobile: Optional[str] = None
    user_password: Optional[str] = None
    user_dp: Optional[str] = None
 
class UserResponse(BaseModel):
    org_id: int
    role: Role
    user_name: str
    user_email: EmailStr
    user_mobile: str
    user_dp: str
 
    class Config:
        orm_mode = True
       
@router.post("/create-users/")
async def create_user(user: UserCreate, db: db_dependency, current_user:str = Depends(get_current_user)):
    # Only HR Admins can create users
    if current_user.role != Role.hr_admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions to create users")
 
    # Check if organization exists
    is_org_found = db.query(Organization).filter(Organization.org_id == user.org_id).first()
    if not is_org_found:
        raise HTTPException(status_code=404, detail="Organization not found")
 
    # Check if email already exists
    user_email_exists = db.query(Users).filter(Users.user_email == user.user_email).first()
    if user_email_exists:
        raise HTTPException(status_code=409, detail="Email is already in use by another user")
 
    # Role authorization checks
    if current_user.role == Role.manager and user.role in [Role.hr_admin, Role.manager]:
        raise HTTPException(status_code=401, detail="Managers cannot create HR Admin or Manager roles")
   
    if current_user.role == Role.member and user.role in [Role.hr_admin, Role.manager]:
        raise HTTPException(status_code=401, detail="Members cannot create HR Admin or Manager roles")
 
    try:
        user_instance = Users(
            org_id=user.org_id,
            role=user.role,
            user_name=user.user_name,
            user_email=user.user_email,
            user_mobile=user.user_mobile,
            user_password=get_password_hash(user.user_password),
            user_dp=user.user_dp,
            timestamp=datetime.utcnow()
        )
 
        db.add(user_instance)
        db.commit()
        db.refresh(user_instance)
 
        payload = {
            "org_id": user_instance.org_id,
            "full_name": user_instance.user_name,
            "login_id": user_instance.user_email,
            "operation": "Created a New User",
        }
 
        return {"detail": "User created successfully", "user": user_instance, "payload": payload}
    except Exception as e:
        # You can use logging here
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
   
   
@router.get("/get-all-users/")
async def get_all_users(db: db_dependency):
    try:
        users = db.query(Users).filter(Users.is_deleted == False).all()
        return jsonable_encoder(users)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
 
@router.get("/get-user-by-id/")
async def get_user_by_id(user_id: int, db: db_dependency):
    user = await check_instance(Users, "user_id", user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        return jsonable_encoder(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
 
@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user: UserUpdate,
    db: db_dependency
):
    user_instance = db.query(Users).filter(Users.user_id == user_id, Users.is_deleted == False).first()
    if not user_instance:
        raise HTTPException(status_code=404, detail="User not found")
 
    # Update fields if provided
    if user.user_name is not None:
        user_instance.user_name = user.user_name
    if user.user_email is not None:
        existing_email_user = db.query(Users).filter(Users.user_email == user.user_email, Users.user_id != user_id).first()
        if existing_email_user:
            raise HTTPException(status_code=409, detail="Email is already in use by another user")
        user_instance.user_email = user.user_email
    if user.user_mobile is not None:
        user_instance.user_mobile = user.user_mobile
    if user.user_password is not None:
        user_instance.user_password = get_password_hash(user.user_password)  # Hash the new password
    if user.user_dp is not None:
        user_instance.user_dp = user.user_dp
 
    db.commit()
    db.refresh(user_instance)
 
    return UserResponse(
        org_id=user_instance.org_id,
        role=user_instance.role,
        user_name=user_instance.user_name,
        user_email=user_instance.user_email,
        user_mobile=user_instance.user_mobile,
        user_dp=user_instance.user_dp
    )
 
@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: db_dependency):
    user_instance = db.query(Users).filter(Users.user_id == user_id, Users.is_deleted == False).first()
    if not user_instance:
        raise HTTPException(status_code=404, detail="User not found")
 
    user_instance.is_deleted = True
    db.commit()
    return {"detail": "User deleted successfully"}
 
@router.get("/get-users-by-org-id/")
async def get_users_by_org_id(org_id: int, db: db_dependency):
    try:
        users = db.query(Users).filter(Users.org_id == org_id, Users.is_deleted == False).all()
       
        if not users:
            raise HTTPException(status_code=404, detail="No users found for the specified organization ID")
       
        return jsonable_encoder(users)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
 
 