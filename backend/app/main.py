from fastapi import FastAPI

app = FastAPI(title="ShramMitra API")


@app.get("/")
def root():
    return {
        "message": "ShramMitra API is running"
    }