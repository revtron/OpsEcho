from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api import events, search, timeline
from db.database import engine
from db.models import Base
from sqlalchemy import text

# Create database tables
Base.metadata.create_all(bind=engine)

# Migrate existing database: add new columns if they don't exist
try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE infrastructure_events ADD COLUMN status VARCHAR DEFAULT 'unknown'"))
        conn.commit()
except Exception:
    pass  # Column already exists

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE infrastructure_events ADD COLUMN severity VARCHAR DEFAULT 'info'"))
        conn.commit()
except Exception:
    pass

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE infrastructure_events ADD COLUMN failure_reason VARCHAR"))
        conn.commit()
except Exception:
    pass

app = FastAPI(title="OpsEcho API", description="Operational Memory Platform")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["timeline"])

@app.get("/")
async def root():
    return {"message": "OpsEcho API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/ai-status")
async def ai_status():
    import httpx
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return {"ai_available": True, "models": models, "provider": "ollama"}
    except Exception:
        pass
    return {
        "ai_available": False,
        "models": [],
        "provider": None,
        "message": "Ollama not running. Install: curl -fsSL https://ollama.com/install.sh | sh  &&  ollama pull phi"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)