from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from jose import JWTError, jwt
from passlib.context import CryptContext
import random
import string

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Import your database connection and models here
from database import connect_db
from models.user import Users

router = APIRouter()

# Secret key, algorithm, and token expiration time
SECRET_KEY = "83daa0256a2289b0fb23693bf1f6034d44396675749244721a2b20e896e11662"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/token")

# Pydantic models for request/response bodies
class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    role: str
    user_id: int
    org_id: int

class TokenData(BaseModel):
    user_name: Optional[str] = None

class UserBase(BaseModel):
    user_name: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(UserBase):
    hashed_password: str

# Utility functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def generate_random_password() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_user(db: Session, user_email: str):
    try:
        user = db.query(Users).filter(Users.user_email == user_email).first()
    except Exception as e:
        user = None
    return user

def authenticate_user(db: Session, user_name: str, password: str):
    user = db.query(Users).filter(Users.user_email == user_name).first()
    print(user)
    if not user:
        raise HTTPException(404, "You don't have an account here. Please create one.")
    if not verify_password(password, user.user_password):
        raise HTTPException(404, "Password is not correct! Try again.")
    return user

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# JWT Authentication and token renewal
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(connect_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name: str = payload.get("sub")
        if user_name is None:
            raise credentials_exception
        token_data = TokenData(user_name=user_name)
    except JWTError:
        raise credentials_exception
    user = get_user(db, user_email=token_data.user_name)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes for login and access token
@router.post("/login/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(connect_db)):
    user = authenticate_user(db, form_data.username, form_data.password)  # 'username' used here instead of 'user_name'
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.user_email, "role": user.role}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.user_id,
            "user_name": user.user_name, "role": user.role, "org_id": user.org_id}

# Protected route example
@router.get("/users/me/", response_model=UserBase)
async def read_users_me(current_user: UserBase = Depends(get_current_active_user)):
    return current_user

# Token verification and renewal
def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_name: str = payload.get("sub")
        if user_name is None:
            raise credentials_exception
        # Reissue token with extended expiration time
        new_expiration = timedelta(hours=24)
        new_token = create_access_token(data={"sub": user_name}, expires_delta=new_expiration)
        return {"token": new_token, "user": payload}
    except JWTError:
        raise credentials_exception

@router.get("/protected-data/")
async def get_protected_data(current_user: dict = Depends(verify_token)):
    return {
        "message": "This is protected data", 
        "user": current_user["user"],
        "new_token": current_user["token"]
    }
