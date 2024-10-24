from database import engine, connect_db, db_dependency
from models.manager import Manager
from .basic_import import *
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from sqlalchemy import func
from typing import List
router = APIRouter()

Manager.metadata.create_all(bind=engine)

class ManagerCreate(BaseModel):
    manager_name: str

class ManagerResponse(BaseModel):
    manager_id: int
    manager_name: str

    class Config:
        orm_mode = True


class ManagerUpdate(BaseModel):
    manager_name: str

    class Config:
        orm_mode = True


@router.post("/manager/", response_model=ManagerResponse)
async def create_manager(manager_data: ManagerCreate, db: db_dependency):
    new_manager = Manager(manager_name=manager_data.manager_name)
    
    db.add(new_manager)
    db.commit()
    db.refresh(new_manager)
    return new_manager

@router.get("/manager/", response_model=List[ManagerResponse])
async def get_managers(db: db_dependency):
    managers = db.query(Manager).all()
    return managers

@router.delete("/manager/{manager_id}", response_model=ManagerResponse)
async def delete_manager(manager_id: int, db: db_dependency):
    manager = db.query(Manager).filter(Manager.manager_id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    db.delete(manager)
    db.commit()
    return manager

@router.patch("/manager/{manager_id}", response_model=ManagerResponse)
async def update_manager(manager_id: int, manager_data: ManagerUpdate, db: db_dependency):
    manager = db.query(Manager).filter(Manager.manager_id == manager_id).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    manager.manager_name = manager_data.manager_name
    db.commit()
    db.refresh(manager)
    return manager
