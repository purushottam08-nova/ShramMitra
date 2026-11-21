import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine

from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from app.api.schemes import router as schemes_router
from app.api.benefits import router as benefits_router
from app.api.documents import router as documents_router
from app.api.applications import router as applications_router
from app.api.grievances import router as grievances_router
from app.api.dashboard import router as dashboard_router
from app.api.notifications import router as notifications_router
from app.api.admin import router as admin_router
from app.api.recommendations import router as recommendations_router

# Import models so SQLAlchemy metadata is registered.
from app.models import (
    User,
    WorkerProfile,
    Scheme,
    Document,
    Application,
    ApplicationStatusHistory,
    Grievance,
    GrievanceStatusHistory,
    SchemeVerificationHistory,
    Notification,
)


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()

configured_origins = os.getenv("CORS_ORIGINS", "").strip()

if configured_origins:
    allowed_origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]
else:
    if APP_ENV == "production":
        raise ValueError(
            "CORS_ORIGINS must be configured in production"
        )

    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

if APP_ENV == "production" and "*" in allowed_origins:
    raise ValueError(
        "Wildcard CORS origins are not allowed in production"
    )


app = FastAPI(
    title="ShramMitra API",
    description="Government benefits and application support platform for gig workers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(schemes_router)
app.include_router(benefits_router)
app.include_router(documents_router)
app.include_router(applications_router)
app.include_router(grievances_router)
app.include_router(dashboard_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(recommendations_router)


@app.get("/")
def root():
    return {
        "message": "ShramMitra API is running",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "database": "unavailable",
            },
        )
