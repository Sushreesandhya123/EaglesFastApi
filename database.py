
from fastapi import Depends
from typing import Annotated
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base,DeclarativeMeta
from sqlalchemy.orm import sessionmaker,Session


connection_string="mysql+pymysql://root:1234@localhost:3306/eagles"
engine=create_engine(connection_string,echo=True)
session_local=sessionmaker(bind=engine,autoflush=False,autocommit=False)

BASE:DeclarativeMeta=declarative_base()

def connect_db():
    db=session_local()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(connect_db)]

