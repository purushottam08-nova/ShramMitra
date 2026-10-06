from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.db.database import Base, engine
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.api.profile import router as profile_router
from app.models.scheme import Scheme
from app.models.scheme_rule import SchemeRule
from app.api.schemes import router as schemes_router
from app.api.benefits import router as benefits_router
from app.api.documents import router as documents_router

app = FastAPI(title="ShramMitra API")
app.include_router(auth_router)
app.include_router(benefits_router)
app.include_router(schemes_router)
app.include_router(documents_router)
app.include_router(profile_router)

@app.get("/")
def root():
    return {
        "message": "ShramMitra API is running"
    }