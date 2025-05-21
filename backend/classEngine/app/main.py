from fastapi import FastAPI
from app.routers import search, feedback

app = FastAPI()
app.include_router(search.router)
app.include_router(feedback.router)