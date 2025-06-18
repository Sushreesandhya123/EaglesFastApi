from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from router import departments,manager,project,employee,performanceparameter,session,organization,sessionentry,performancerating
from router.users import user,login


app = FastAPI(title="Eagles")


app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],
   allow_credentials=True,
   allow_methods=["*"],
   allow_headers=["*"],
)
app.include_router(
    login.router,
    tags=["Login"],
    prefix="/Login"
)

app.include_router(
    departments.router,
    tags=["Departments"],
    prefix="/Departments"
)
app.include_router(
    manager.router,
    tags=["Manager"],
    prefix="/Manager"
)
app.include_router(
    project.router,
    tags=["Project"],
    prefix="/Project"
)
app.include_router(
    employee.router,
    tags=["Employee"],
    prefix="/Employee"
)
app.include_router(
    performanceparameter.router,
    tags=["PerformanceParameter"],
    prefix="/PerformanceParameter"
)

app.include_router(
    session.router,
    tags=["Session"],
    prefix="/Session"
)
app.include_router(
    organization.router,
    tags=["Organization"],
    prefix="/Organization"
)
app.include_router(
    sessionentry.router,
    tags=["SessionEntry"],
    prefix="/SessionEntry"
)
app.include_router(
    performancerating.router,
    tags=["PerformanceRating"],
    prefix="/PerformanceRating"
)
app.include_router(
    user.router,
    tags=["User"],
    prefix="/User"
)