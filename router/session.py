from database import engine, connect_db, db_dependency
from models.session import SessionModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
# from datetime import date
from datetime import date as current_date
from typing import Optional
from datetime import datetime, date

router = APIRouter()
SessionModel.metadata.create_all(bind=engine)

# Pydantic schema for creating a session (POST request)
class SessionCreate(BaseModel):
    session_name: str
    start_date: current_date
    end_date: current_date

# Pydantic schema for reading session data (GET response)
class SessionRead(BaseModel):
    session_id: int
    session_name: str
    start_date: current_date
    end_date: current_date
    status: str

    class Config:
        orm_mode = True  # Enable ORM mode to work with SQLAlchemy models

# Pydantic schema for updating a session (PATCH request)
class SessionUpdate(BaseModel):
    session_name: Optional[str] = None
    start_date: Optional[current_date] = None
    end_date: Optional[current_date] = None        


def determine_status(start_date: date, end_date: date) -> str:
    today = datetime.today().date()  # Get today's date
    
    # Normalize to date for comparison
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Check if the session is created today
    if start_date == today:
        return "New"  # The session is newly created today
    elif start_date <= today <= end_date:
        return "Active"  # The session is currently ongoing
    elif today > end_date:
        return "Closed"  # The session has ended
    else:
        return "New" 

# POST: Create a new session
@router.post("/sessions/", response_model=SessionRead)
def create_session(session_data: SessionCreate, db: db_dependency):
    status = determine_status(session_data.start_date, session_data.end_date)

    # Create a new session object with the calculated status
    db_session = SessionModel(
        session_name=session_data.session_name,
        start_date=session_data.start_date,
        end_date=session_data.end_date,
        status=status
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

# GET: Fetch all sessions
@router.get("/sessions/", response_model=List[SessionRead])
def read_sessions(db: db_dependency):
    sessions = db.query(SessionModel).all()
    return sessions

# DELETE: Delete a session by session_id
@router.delete("/sessions/{session_id}", response_model=SessionRead)
def delete_session(session_id: int, db: db_dependency):
    db_session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(db_session)
    db.commit()
    return db_session

# PATCH: Update a session by session_id
@router.patch("/sessions/{session_id}", response_model=SessionRead)
def update_session(session_id: int, session_data: SessionUpdate, db: db_dependency):
    db_session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    
    if db_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update fields if provided
    if session_data.session_name is not None:
        db_session.session_name = session_data.session_name
    if session_data.start_date is not None:
        db_session.start_date = session_data.start_date
    if session_data.end_date is not None:
        db_session.end_date = session_data.end_date

    # Recalculate status based on updated dates
    db_session.status = determine_status(db_session.start_date, db_session.end_date)

    db.commit()
    db.refresh(db_session)
    return db_session
