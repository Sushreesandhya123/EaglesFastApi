from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import engine, db_dependency
from models.sessionentry import SessionEntryModal
from models.organization import Organization  # Removed RoleEnum import
from models.session import SessionModel
from models.employee import Employee
from sqlalchemy.orm import aliased
from datetime import date as current_date
from models.performanceparameter import PerformanceParameter
from models.performancerating import PerformanceRating
from sqlalchemy import and_, or_

session = Session()
import logging

logging.basicConfig(level=logging.INFO)

router = APIRouter()
SessionEntryModal.metadata.create_all(bind=engine)

class SessionEntryCreate(BaseModel):
    emp_id: int 
    session_id: Optional[int] 
    parameter_id: int
    rating: int
    comments: Optional[str] = None
@router.post("/session-entry/")
def create_session_entry(session_entry: SessionEntryCreate, db:db_dependency):
    try:
        new_entry = SessionEntryModal(
            session_id=session_entry.session_id,  # Use session_id from the request
            emp_id=session_entry.emp_id,
            parameter_id=session_entry.parameter_id,
            rating=session_entry.rating,
            comments=session_entry.comments
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return {"message": "Session entry created successfully!", "session_entry": new_entry}
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating session entry: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
@router.get("/api/sessions")
def read_sessions(db: db_dependency):
    return db.query(SessionModel).all()

@router.get("/api/employees")
def read_employees(session_id: int, db: db_dependency):
    return db.query(Employee).filter(Employee.department_id == session_id).all()  # Adjust based on your logic

@router.post("/api/submit")
def submit_rating(emp_id: int, session_id: int,parameter_id: int, db: db_dependency,rating: int, comments: str = None):
    # Create a new performance rating
    new_rating = PerformanceRating(emp_id=emp_id, session_id=session_id,parameter_id=parameter_id, rating=rating, comments=comments)
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return {"message": "Rating submitted successfully!", "rating_id": new_rating.rating_id}



