from datetime import timedelta
from router.basic_import import *
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy.orm import Session
from models.organization import Organization
from models.user import Users
from database import engine, connect_db, db_dependency
from router.users.login import get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
 
from enum import Enum
import re
 
router = APIRouter()
 
Organization.metadata.create_all(bind=engine)
 
class Role(str, Enum):
    member = "Member"
    manager = "Manager"
    hr_admin = "HR Admin"
 
 
class OrganizationBase(BaseModel):
    org_name: str = Field(default="Cultfit")
    org_mobile_number: str = Field(max_length=10, min_length=10, default="9876543210")
    org_email: EmailStr = Field(default="example@gmail.com")
    org_address: str = Field(default="")
    org_pincode: str = Field(default="")
    org_city: str = Field(default="")
    org_state: str = Field(default="")
    org_country: str = Field(default="")
    org_logo: str = None
    password: str = Field(default="")
    full_name: str = Field(default="Rupashree")
 
    @validator("org_mobile_number")
    def validate_mobile_number(cls, v):
        if not re.match(r'^[6-9][0-9]{9}$', v):
            raise ValueError("Mobile number must be 10 digits and start with 6-9")
        return v
 
 
async def create_super_user(db, user: dict):
    user_instance = Users(**user)
    user_instance.timestamp = await get_current_ist_time()
    user_instance.user_password = get_password_hash(user["user_password"])
    db.add(user_instance)
    db.commit()
    db.refresh(user_instance)
 
    login_data = await auto_login(user_instance.__dict__)
    return login_data
 
 
async def auto_login(user: dict):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["user_email"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "user_name": user["user_name"],
        "role": user["role"],
        "org_id": user["org_id"]
    }
 
 
@router.post("/create-organization/")
async def create_organization(org: OrganizationBase, db: db_dependency):
    try:
        # Check if email or phone number already exists
        is_email_found = await check_instance(Organization, "org_email", org.org_email, db)
        if is_email_found:
            raise HTTPException(status_code=409, detail="Email already exists")
        is_phone_found = await check_instance(Organization, "org_mobile_number", org.org_mobile_number, db)
        if is_phone_found:
            raise HTTPException(status_code=409, detail="Phone number already exists")
 
        # Create organization instance
        org_instance = Organization(**org.dict())
        org_instance.org_logo = 'https://example.com/default_logo.png'  # Default logo
        org_instance.password = get_password_hash(org.password)
       
        db.add(org_instance)
        db.commit()
        db.refresh(org_instance)
 
        payload = {
            "org_id": org_instance.org_id,
            "role": Role.hr_admin.value,
            "user_name": org_instance.full_name,
            "user_email": org_instance.org_email,
            "user_mobile": org_instance.org_mobile_number,
            "user_password": org_instance.password
        }
 
        login_data = await create_super_user(db, payload)
        login_data["org_logo"] = org_instance.org_logo
       
 
        return succes_response(login_data, "Organization created successfully")
 
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {e}"
        )
 
 
@router.get("/get-all-organization/")
async def get_all_organization(db: db_dependency):
    organizations = db.query(Organization).all()
    return {"organizations": organizations}
 
 
@router.get("/get-organization/{org_id}")
async def get_organization(org_id: int, db: db_dependency):
    org = db.query(Organization).filter(Organization.org_id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization Not Found")
    return org
 
 
@router.patch("/update-organization/{org_id}")
async def update_organization(org_id: int, org_base: OrganizationBase, db: db_dependency):
    org = await check_instance(Organization, "org_id", org_id, db)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
 
    # Update organization fields
    for key, value in org_base.dict(exclude_unset=True).items():
        setattr(org, key, value)
    if org_base.org_logo and org_base.org_logo != "":
        org.org_logo = org_base.org_logo
 
    if org_base.password:
        org.password = org_base.password
 
    db.commit()
    db.refresh(org)
 
    user = db.query(Users).filter(Users.org_id == org_id).first()
    if user:
        if org_base.full_name:
            user.user_name = org_base.full_name
        if org_base.org_email:
            user.user_email = org_base.org_email
        if org_base.org_mobile_number:
            user.user_mobile = org_base.org_mobile_number
        if org_base.password:
            user.user_password = Users.hash_password(org_base.password)
 
        db.commit()
        db.refresh(user)
 
    return succes_response(data=org, msg="Organization updated successfully.")
 
 
@router.get("/get-all-organization/")
async def get_all_organization(db:db_dependency):
    organizations = db.query(Organization).all()
    return {"organizations": organizations}
 
@router.get("/get-organization/{org_id}")
async def get_organization(org_id: int, db:db_dependency):
    org = db.query(Organization).filter(Organization.org_id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization Not Found")
    return org
 
# @router.patch("/update-organization/{org_id}")
# async def update_organization(org_id: int, org_base: OrganizationBase, db: db_dependency):
#     org = await check_instance(Organization, "org_id", org_id, db)
#     if org is None:
#         raise HTTPException(status_code=404, detail="Organization not found")
 
#     # Update organization fields
#     for key, value in org_base.dict(exclude_unset=True).items():
#         setattr(org, key, value)
#     if org_base.org_logo and org_base.org_logo != "":
#         org.org_logo = org_base.org_logo
   
#     if org_base.password:
#         org.password = org_base.password
   
#     db.commit()
#     db.refresh(org)
#     user = db.query(Users).filter(Users.org_id == org_id).first()
#     if user:
#         if org_base.full_name:
#             user.user_name = org_base.full_name
#         if org_base.org_email:
#             user.user_email = org_base.org_email
#         if org_base.org_mobile_number:
#             user.user_mobile = org_base.org_mobile_number
#         if org_base.password:
#             user.user_password = Users.hash_password(org_base.password)
       
#         db.commit()
#         db.refresh(user)
 
       
#     return succes_response(data=org, msg="Organization updated successfully.")