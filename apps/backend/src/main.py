from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.api import patient_triage_ws, router

app = FastAPI(title="TriageFlow API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket endpoint needs to be on the app directly, not through router
@app.websocket("/api/ws/agents/patient/triage/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await patient_triage_ws(websocket, session_id)


app.include_router(router, prefix="/api/agents", tags=["agents"])
