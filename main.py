from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, sites, cameras, events, ws, users, agents

app = FastAPI(title="Hostel Security API", version="0.1.0")

# MVP CORS: tighten later
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "hostel-sec-api", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(sites.router, prefix="/sites", tags=["sites"])
app.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(ws.router, prefix="/ws", tags=["ws"])