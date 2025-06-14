from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import router

app = FastAPI(title="TriageFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/agents", tags=["agents"])
