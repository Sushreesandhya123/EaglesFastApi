from fastapi import FastAPI, HTTPException, Depends,APIRouter
from sqlalchemy.orm import Session
from database import engine, connect_db, db_dependency
from models.employee import Employee
from models.session import SessionModel
from models.performanceparameter import PerformanceParameter
from models.performancerating import PerformanceRating
from pydantic import BaseModel
from typing import List

router = APIRouter()
PerformanceRating.metadata.create_all(bind=engine)


# Pydantic models for data validation
class SessionCreate(BaseModel):
    name: str
    start_date: str
    end_date: str

# Pydantic model for session response
class SessionResponse(BaseModel):
    id: int
    name: str
    start_date: str
    end_date: str
    status: str

# Pydantic model for employee performance response
class EmployeePerformance(BaseModel):
    emp_id: int
    name: str
    designation: str
    parameters: List[dict]

# Pydantic model for rating submission
class RatingSubmission(BaseModel):
    ratings: List[dict]

# 1. Session Creation by HR (with email notification to managers)

@router.get("/session/{session_id}/employees", response_model=List[EmployeePerformance])
def get_employees_for_session(session_id: int, manager_name: str, db:db_dependency):
    employees = db.query(Employee).filter(Employee.manager_name == manager_name).all()

    if not employees:
        raise HTTPException(status_code=404, detail="No employees found for this manager")

    employee_performance_list = []
    for emp in employees:
        parameters = db.query(PerformanceParameter).all()

        employee_performance_list.append({
            "emp_id": emp.emp_id,
            "name": emp.employee_name,
            "designation": emp.designation,
            "parameters": [{"id": p.parameter_id, "name": p.name} for p in parameters]
        })

    return employee_performance_list

# 4. Submit Performance Rating
@router.post("/session/{session_id}/rate")
def submit_performance_rating(session_id: int, rating_submission: RatingSubmission, manager_name: str, db:db_dependency):
    # For each rating in the submission, create a performance rating
    for rating in rating_submission.ratings:
        emp_id = rating["emp_id"]
        for param_rating in rating["ratings"]:
            new_rating = PerformanceRating(
                emp_id=emp_id,
                parameter_id=param_rating["parameter_id"],
                session_id=session_id,
                rating=param_rating["rating"],
                comments=param_rating.get("comments", "")
            )
            db.add(new_rating)

    db.commit()
    return {"message": "Ratings submitted successfully"}

class RatingSubmission(BaseModel):
    employee_id: int
    rating: int
    comments: str

@router.post("/sessions/{session_id}/submit")
def submit_ratings(session_id: int, manager_id: int, ratings: list[RatingSubmission], db:db_dependency):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if the session is assigned to the manager
    assignment = db.query(SessionModel).filter_by(session_id=session_id, manager_id=manager_id).first()
    if not assignment:
        raise HTTPException(status_code=403, detail="You are not assigned to this session")

    for rating_data in ratings:
        employee = db.query(Employee).filter(Employee.id == rating_data.employee_id).first()
        if employee.manager_id != manager_id:
            raise HTTPException(status_code=403, detail=f"Unauthorized to rate employee {employee.name}")

        rating = PerformanceRating(
            session_id=session_id,
            employee_id=rating_data.employee_id,
            rating=rating_data.rating,
            comments=rating_data.comments
        )
        db.add(rating)

    db.commit()

    return {"message": "Ratings submitted successfully"}