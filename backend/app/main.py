from fastapi import FastAPI
from app.db.database import engine

app = FastAPI(title="ShramMitra API")


@app.get("/")
def root():
    return {
        "message": "ShramMitra API is running"
    }


@app.get("/db-test")
def db_test():
    try:
        with engine.connect() as connection:
            return {
                "message": "Database connected successfully"
            }
    except Exception as e:
        return {
            "message": "Database connection failed",
            "error": str(e)
        }