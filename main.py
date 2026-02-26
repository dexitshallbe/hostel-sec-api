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

app.include_router(auth.router)
app.include_router(sites.router)
app.include_router(cameras.router)
app.include_router(events.router)
app.include_router(ws.router)
app.include_router(users.router)
app.include_router(agents.router)

@app.get("/health")
def health():
    return {"ok": True}