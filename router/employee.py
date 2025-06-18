from database import engine, db_dependency
from models.employee import Employee
from models.project import Project
from models.departments import Department
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

router = APIRouter(
    prefix="/employees",
    tags=["employees"]
)

# Ensure the Employee table is created
Employee.metadata.create_all(bind=engine)

# Enum for role types
class RoleEnum(str, Enum):
    member = "Member"
    manager = "Manager"
    hr_admin = "HR Admin"

# Schema for updating an employee
class EmployeeUpdate(BaseModel):
    employee_name: Optional[str] = Field(None, min_length=1, max_length=100)
    designation: Optional[str] = Field(None, min_length=1, max_length=50)
    role: Optional[RoleEnum] = None
    project_name: Optional[str] = None
    manager_name: Optional[str] = None

    class Config:
        orm_mode = True

# Schema for the response
class EmployeeResponse(BaseModel):
    employee_id: str
    emp_id: int
    employee_name: str
    designation: str
    project_name: Optional[str] = None
    role: RoleEnum
    manager_name: Optional[str] = None
    department_name: Optional[str] = None

class ManagerResponse(BaseModel):
    employee_name: str    

    class Config:
        orm_mode = True

# Helper functions
def validate_project_name(db: Session, project_name: str):
    project = db.query(Project).filter(Project.project_name == project_name).first()
    if not project:
        raise HTTPException(status_code=400, detail="Project does not exist")

def validate_manager_name(db: Session, role: RoleEnum, manager_name: Optional[str]):
    if role in [RoleEnum.hr_admin, RoleEnum.manager]:
        return True
    elif role == RoleEnum.member:
        managers = db.query(Employee).filter(Employee.role == RoleEnum.manager).all()
        manager_names = [manager.employee_name for manager in managers]
        if manager_name not in manager_names:
            raise HTTPException(status_code=400, detail="Member must have a Manager as manager name")

# Create employee schema
class EmployeeCreate(BaseModel):
    employee_id: str
    employee_name: str
    designation: str
    role: RoleEnum
    project_name: Optional[str] = None
    manager_name: Optional[str] = None
    department_name: Optional[str] = None

# Create a new employee
@router.post("/", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: db_dependency):
    if db.query(Employee).filter(Employee.employee_id == employee.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee with this ID already exists")

    if employee.manager_name:
        validate_manager_name(db, employee.role, employee.manager_name)

    project_id = None
    if employee.project_name:
        project = db.query(Project).filter(Project.project_name == employee.project_name).first()
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        project_id = project.project_id

    department_id = None
    if employee.department_name:
        department = db.query(Department).filter(Department.department_name == employee.department_name).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department does not exist")
        department_id = department.department_id

    new_employee = Employee(
        employee_id=employee.employee_id,
        employee_name=employee.employee_name,
        designation=employee.designation,
        role=employee.role,
        department_id=department_id,
        project_id=project_id,
        manager_name=employee.manager_name
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    return EmployeeResponse(
        employee_id=new_employee.employee_id,
        emp_id=new_employee.emp_id,
        employee_name=new_employee.employee_name,
        designation=new_employee.designation,
        project_name=employee.project_name,
        role=new_employee.role,
        manager_name=new_employee.manager_name,
        department_name=employee.department_name
    )

# Get employee by emp_id
@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int, db: db_dependency):
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    project_name = None
    if employee.project_id:
        project = db.query(Project).filter(Project.project_id == employee.project_id).first()
        project_name = project.project_name if project else None

    department_name = employee.department.department_name if employee.department else None

    return EmployeeResponse(
        employee_id=employee.employee_id,
        emp_id=employee.emp_id,
        employee_name=employee.employee_name,
        designation=employee.designation,
        project_name=project_name,
        role=employee.role,
        manager_name=employee.manager_name,
        department_name=department_name
    )

# Update employee
@router.patch("/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, employee_update: EmployeeUpdate, db: db_dependency):
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee_update.manager_name and employee_update.role:
        validate_manager_name(db, employee_update.role, employee_update.manager_name)

    project_id = None
    if employee_update.project_name:
        validate_project_name(db, employee_update.project_name)
        project = db.query(Project).filter(Project.project_name == employee_update.project_name).first()
        project_id = project.project_id

    if employee_update.employee_name:
        employee.employee_name = employee_update.employee_name
    if employee_update.designation:
        employee.designation = employee_update.designation
    if employee_update.role:
        employee.role = employee_update.role
    if employee_update.project_name:
        employee.project_id = project_id
    if employee_update.manager_name:
        employee.manager_name = employee_update.manager_name

    db.commit()
    db.refresh(employee)

    # Get updated project name for response
    updated_project_name = None
    if employee.project_id:
        project = db.query(Project).filter(Project.project_id == employee.project_id).first()
        updated_project_name = project.project_name if project else None

    return EmployeeResponse(
        employee_id=employee.employee_id,
        emp_id=employee.emp_id,
        employee_name=employee.employee_name,
        designation=employee.designation,
        project_name=updated_project_name,
        role=employee.role,
        manager_name=employee.manager_name,
        department_name=employee.department.department_name if employee.department else None
    )

# Delete employee
@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: db_dependency):
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.delete(employee)
    db.commit()
    return {"message": f"Employee with ID {emp_id} deleted successfully"}

# Get all employees
@router.get("/", response_model=List[EmployeeResponse])
def get_all_employees(db: db_dependency):
    employees = db.query(Employee).all()

    employee_responses = []
    for employee in employees:
        project_name = None
        if employee.project_id:
            project = db.query(Project).filter(Project.project_id == employee.project_id).first()
            project_name = project.project_name if project else None

        department_name = employee.department.department_name if employee.department else None

        employee_responses.append(EmployeeResponse(
            employee_id=employee.employee_id,
            emp_id=employee.emp_id,
            employee_name=employee.employee_name,
            designation=employee.designation,
            project_name=project_name,
            role=employee.role,
            manager_name=employee.manager_name,
            department_name=department_name
        ))

    return employee_responses

# Get all managers
@router.get("/managers/", response_model=List[ManagerResponse])
def get_managers(db: db_dependency):
    managers = db.query(Employee).filter(Employee.role == RoleEnum.manager).all()
   
    if not managers:
        raise HTTPException(status_code=404, detail="No managers found")
   
    return [ManagerResponse(employee_name=manager.employee_name) for manager in managers]