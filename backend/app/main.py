from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.db.database import Base, engine
from app.models.user import User
from app.models.worker_profile import WorkerProfile


Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShramMitra API")

app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "ShramMitra API is running"
    }