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
app.include_router(auth.router, tags=["auth"])
app.include_router(users.router, tags=["users"])
app.include_router(sites.router, tags=["sites"])
app.include_router(cameras.router, tags=["cameras"])
app.include_router(events.router, tags=["events"])
app.include_router(agents.router, tags=["agents"])
app.include_router(ws.router, tags=["ws"])