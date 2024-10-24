from database import engine, connect_db, db_dependency
from models.departments import Department
from models.employee import Employee
from models.project import Project
from .basic_import import *
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import func
from typing import List
router = APIRouter()

Department.metadata.create_all(bind=engine)

class DepartmentCreate(BaseModel):
    department_name: str

class DepartmentResponse(BaseModel):
    department_id: int
    department_name: str

    class Config:
        orm_mode = True

class DepartmentUpdate(BaseModel):
    department_name: str

    class Config:
        orm_mode = True



# POST operation: Create a new department
@router.post("/departments/", response_model=DepartmentResponse)
async def create_department(department_data: DepartmentCreate, db: db_dependency):
    new_department = Department(department_name=department_data.department_name)
    
    db.add(new_department)
    db.commit()
    db.refresh(new_department)
    return new_department



# DELETE operation: Delete a department by ID
@router.delete("/departments/{department_id}")
async def delete_department(department_id: int, db: db_dependency):
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Deleting the department will automatically delete related employees and projects due to the cascade setting
    db.delete(department)
    db.commit()
    return {"message": f"Department with ID {department_id} has been deleted successfully"}

# PATCH operation: Update a department name by ID
@router.patch("/departments/{department_id}", response_model=DepartmentResponse)
async def update_department(department_id: int, department_data: DepartmentUpdate, db: db_dependency):
    department = db.query(Department).filter(Department.department_id == department_id).first()
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    
    department.department_name = department_data.department_name
    db.commit()
    db.refresh(department)
    return department

@router.get("/departments/", response_model=List[DepartmentResponse])
async def get_departments(db: db_dependency):
    departments = db.query(Department).all()
    return departments


@router.get("/departments")
def get_departments(db: db_dependency):
    departments = db.query(Department).all()
    result = []
    
    for department in departments:
        total_projects = len(department.projects)
        total_employees = len(department.employees)
        
        result.append({
            "department_id": department.department_id,
            "department_name": department.department_name,
            "total_projects": total_projects,
            "total_employees": total_employees
        })
    
    return result