from database import engine, db_dependency
from models.employee import Employee
from models.project import Project
from models.departments import Department
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
 
router = APIRouter()
 
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
    manager_name: Optional[str] = None  # Include manager name if applicable
 
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
    department_name: Optional[str] = None  # Add this line to include department name
 
class ManagerResponse(BaseModel):
    employee_name: str    
 
    class Config:
        orm_mode = True
 
# Helper function to fetch department_id by name
def get_department_id_by_name(db: Session) -> int:
    # Set a default department_id, e.g., 1 or another application logic
    return 1
 
# Helper function to validate if the project name exists
def validate_project_name(db: Session, project_name: str):
    project = db.query(Project).filter(Project.project_name == project_name).first()
    if not project:
        raise HTTPException(status_code=400, detail="Project does not exist")
 
# Helper function to validate manager name based on the role
def validate_manager_name(db: Session, role: RoleEnum, manager_name: Optional[str]):
    if role in [RoleEnum.hr_admin, RoleEnum.manager]:
        return True  # HR Admin and Manager can have any manager name
    elif role == RoleEnum.member:
        # Only allow Manager names
        managers = db.query(Employee).filter(Employee.role == RoleEnum.manager).all()
        manager_names = [manager.employee_name for manager in managers]
        if manager_name not in manager_names:
            raise HTTPException(status_code=400, detail="Member must have a Manager as manager name")
 
# Update the EmployeeCreate schema to include department_name
class EmployeeCreate(BaseModel):
    employee_id: str  # Unique employee ID (not primary key)
    employee_name: str
    designation: str
    role: RoleEnum  # Role can be 'Member', 'Manager', 'HR Admin'
    project_name: Optional[str] = None  # Users pass project_name instead of project_id
    manager_name: Optional[str] = None  # Users can provide manager name
    department_name: Optional[str] = None  # Accept department name
 
# Create a new employee
# Create a new employee
@router.post("/employees/", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: db_dependency):
    # Check if the employee ID already exists
    if db.query(Employee).filter(Employee.employee_id == employee.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee with this ID already exists")
 
    # Validate manager_name based on role
    if employee.manager_name:  # Only validate if manager_name is provided
        validate_manager_name(db, employee.role, employee.manager_name)
 
    # Handle project creation or fetch project ID if project name is provided
    project_id = None
    if employee.project_name:
        project = db.query(Project).filter(Project.project_name == employee.project_name).first()
        if project is None:
            raise HTTPException(status_code=400, detail="Project not found")
        project_id = project.project_id
 
    # Fetch department_id by name if department_name is provided
    department_id = None
    if employee.department_name:
        department = db.query(Department).filter(Department.department_name == employee.department_name).first()
        if not department:
            raise HTTPException(status_code=400, detail="Department does not exist")
        department_id = department.department_id
 
    # Create new employee instance
    new_employee = Employee(
        employee_id=employee.employee_id,
        employee_name=employee.employee_name,
        designation=employee.designation,
        role=employee.role,
        department_id=department_id,  # Use the fetched department ID
        project_id=project_id,  # Use the project ID
        manager_name=employee.manager_name  # Set manager_name (if provided)
    )
 
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
 
    return EmployeeResponse(
        employee_id=new_employee.employee_id,
        emp_id=new_employee.emp_id,
        employee_name=new_employee.employee_name,
        designation=new_employee.designation,
        project_name=employee.project_name,  # Return the project name as it was passed
        role=new_employee.role,
        manager_name=new_employee.manager_name,  # Return the manager name (if provided)
        department_name=employee.department_name  # Return the provided department name
    )
 
 
# Update an employee by ID
@router.patch("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, employee_update: EmployeeUpdate, db: db_dependency):
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
 
    # Validate manager_name if it's being updated
    if employee_update.manager_name and employee_update.role:
        validate_manager_name(db, employee_update.role, employee_update.manager_name)
 
    # Validate project_name if it's being updated
    if employee_update.project_name:
        validate_project_name(db, employee_update.project_name)
 
    # Update fields if provided
    if employee_update.employee_name:
        employee.employee_name = employee_update.employee_name
    if employee_update.designation:
        employee.designation = employee_update.designation
    if employee_update.role:
        employee.role = employee_update.role
    if employee_update.project_name:
        employee.project_name = employee_update.project_name  # Store project_name directly
    if employee_update.manager_name:
        employee.manager_name = employee_update.manager_name
 
    # Commit changes
    db.commit()
    db.refresh(employee)
 
    return EmployeeResponse(
        employee_id=employee.employee_id,
        emp_id=employee.emp_id,
        employee_name=employee.employee_name,
        designation=employee.designation,
        project_name=employee.project_name,  # Directly return updated project name
        role=employee.role,
        manager_name=employee.manager_name  # Return the updated manager name
    )
 
# Get an employee by ID
@router.get("/employees/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int, db: db_dependency):
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
 
    # Get department name if available
    department_name = employee.department.department_name if employee.department else None
 
    return EmployeeResponse(
        employee_id=employee.employee_id,
        emp_id=employee.emp_id,
        employee_name=employee.employee_name,
        designation=employee.designation,
        project_name=employee.project_name,
        role=employee.role,
        manager_name=employee.manager_name,
        department_name=department_name  # Include the department name in the response
    )
 
# Delete an employee by ID
@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: int, db: db_dependency):
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
 
    db.delete(employee)
    db.commit()
    return {"message": f"Employee with ID {emp_id} deleted successfully"}
 
 
# Get all employees
@router.get("/employees/", response_model=List[EmployeeResponse])
def get_all_employees(db: db_dependency):
    employees = db.query(Employee).all()
 
    employee_responses = []
    for employee in employees:
        project_name = None
        if employee.project_id:
            project = db.query(Project).filter(Project.project_id == employee.project_id).first()
            project_name = project.project_name if project else None
 
        # Get department name if available
        department_name = employee.department.department_name if employee.department else None
 
        employee_responses.append(EmployeeResponse(
            employee_id=employee.employee_id,
            emp_id=employee.emp_id,
            employee_name=employee.employee_name,
            designation=employee.designation,
            project_name=project_name,
            role=employee.role,
            manager_name=employee.manager_name,
            department_name=department_name  # Include department name in response
        ))
 
    return employee_responses
 
@router.get("/managers/", response_model=List[ManagerResponse])
def get_managers(db: db_dependency):
    managers = db.query(Employee).filter(Employee.role == RoleEnum.manager).all()
   
    if not managers:
        raise HTTPException(status_code=404, detail="No managers found")
   
    return [ManagerResponse(employee_name=manager.employee_name) for manager in managers]
