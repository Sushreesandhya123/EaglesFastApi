from database import engine, connect_db, db_dependency
from models.performanceparameter import PerformanceParameter
from .basic_import import *
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import func
from typing import List
router = APIRouter()

PerformanceParameter.metadata.create_all(bind=engine)


class PerformanceParameterCreate(BaseModel):
    name: str
    min_rating: int
    max_rating: int

# Response model for returning PerformanceParameter
class PerformanceParameterResponse(BaseModel):
    parameter_id: int
    name: str
    min_rating: int
    max_rating: int

    class Config:
        orm_mode = True

# POST operation to create a new performance parameter
@router.post("/parameters", response_model=PerformanceParameterResponse)
def create_performance_parameter(parameter_data: PerformanceParameterCreate, db: db_dependency):
    new_parameter = PerformanceParameter(
        name=parameter_data.name,
        min_rating=parameter_data.min_rating,
        max_rating=parameter_data.max_rating
    )
    db.add(new_parameter)
    db.commit()
    db.refresh(new_parameter)
    return new_parameter

# GET operation to retrieve all performance parameters
@router.get("/parameters", response_model=List[PerformanceParameterResponse])
def get_performance_parameters(db: db_dependency):
    parameters = db.query(PerformanceParameter).all()
    return parameters

# GET operation to retrieve a single performance parameter by id
@router.get("/parameters/{parameter_id}", response_model=PerformanceParameterResponse)
def get_performance_parameter(parameter_id: int, db: db_dependency):
    parameter = db.query(PerformanceParameter).filter(PerformanceParameter.parameter_id == parameter_id).first()
    if not parameter:
        raise HTTPException(status_code=404, detail="Performance parameter not found")
    return parameter

# PATCH operation to update a performance parameter by id
@router.patch("/parameters/{parameter_id}", response_model=PerformanceParameterResponse)
def update_performance_parameter(
    parameter_id: int, 
    parameter_data: PerformanceParameterCreate, 
    db: db_dependency
):
    parameter = db.query(PerformanceParameter).filter(PerformanceParameter.parameter_id == parameter_id).first()
    
    if not parameter:
        raise HTTPException(status_code=404, detail="Performance parameter not found")
    
    parameter.name = parameter_data.name
    parameter.min_rating = parameter_data.min_rating
    parameter.max_rating = parameter_data.max_rating

    db.commit()
    db.refresh(parameter)
    
    return parameter

# DELETE operation to delete a performance parameter by id
@router.delete("/parameters/{parameter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_performance_parameter(parameter_id: int, db: db_dependency):
    parameter = db.query(PerformanceParameter).filter(PerformanceParameter.parameter_id == parameter_id).first()

    if not parameter:
        raise HTTPException(status_code=404, detail="Performance parameter not found")

    db.delete(parameter)
    db.commit()

    return {"detail": "Performance parameter deleted successfully"}