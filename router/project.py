from database import engine, connect_db, db_dependency
from models.project import Project
from models.employee import Employee
from models.departments import Department
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session,joinedload
from pydantic import BaseModel
from typing import List
 
router = APIRouter()
Project.metadata.create_all(bind=engine)
 
class ProjectCreate(BaseModel):
    project_name: str
    department_name: str
    employee_ids: List[int] = []  # Optional list of employee IDs to associate with the project

class ProjectUpdate(BaseModel):
    project_name: str = None  
    department_name: str = None 

class ProjectResponse(BaseModel):
    project_id: int  # Assuming project_id is the primary key
    project_name: str
    department_name: str
    total_employees: int

    class Config:
        orm_mode = True    

# GET endpoint to retrieve all projects
@router.get("/projects/", response_model=List[ProjectResponse])
async def read_projects(db:db_dependency):
    projects = db.query(Project).all()
    return [
        ProjectResponse(
            project_id=project.project_id,
            project_name=project.project_name,
            department_name=project.department.department_name if project.department else "Unknown",
            total_employees=len(project.employees)  # Calculate total employees from the relationship
        ) for project in projects
    ]

# DELETE endpoint to remove a project
@router.delete("/projects/{project_id}", response_model=dict)
async def delete_project(project_id: int, db:db_dependency):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Optionally, handle associated employees (e.g., unassign or delete)
    for employee in project.employees:
        employee.project_id = None  # Unassign employees from the project, or handle accordingly

    db.delete(project)
    db.commit()
    return {"detail": "Project deleted successfully"}

# PATCH endpoint to update an existing project
@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_update: ProjectUpdate, db:db_dependency):
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update project fields if provided
    if project_update.project_name:
        project.project_name = project_update.project_name

    if project_update.department_name:
        department = db.query(Department).filter(Department.department_name == project_update.department_name).first()
        if department:
            project.department_id = department.department_id  # Update only if department exists
        else:
            raise HTTPException(status_code=400, detail="Department not found")

    db.commit()
    db.refresh(project)

    return ProjectResponse(
        project_id=project.project_id,
        project_name=project.project_name,
        department_name=department.department_name if department else "Unknown",
        total_employees=len(project.employees)  # Calculate total employees after update
    )

# POST endpoint to create a new project
# POST endpoint to create a new project
@router.post("/projects/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: db_dependency):
    # Check if the department exists
    department = db.query(Department).filter(Department.department_name == project.department_name).first()
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")

    # Create the new project
    new_project = Project(project_name=project.project_name, department_id=department.department_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)  # Refresh to get the updated project including its ID

    # Associate employees if provided
    if project.employee_ids:
        for emp_id in project.employee_ids:
            employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
            if employee:
                employee.project_id = new_project.project_id  # Associate employee with the new project

    db.commit()  # Commit changes

    # Fetch the project again to get the updated employee count
    updated_project = db.query(Project).options(
        joinedload(Project.employees)
    ).filter(Project.project_id == new_project.project_id).first()

    # Calculate total employees (if you've set up the relationship)
    total_employees = len(updated_project.employees) if updated_project else 0

    return ProjectResponse(
        project_id=updated_project.project_id,
        project_name=updated_project.project_name,
        department_name=department.department_name,
        total_employees=total_employees
    )
