from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_NAME, APP_TAGLINE, MATCHER_TYPE, BASE_DIR
from app.database import engine, Base
from app.migrations import run_migrations
from app.routes import auth, profile, events, seats, invites, teams, feedback, safety, icebreaker
from app.routes import meta, students, join_requests
from app.routes import (
    opportunities, jobs, resumes, applications, learn, certificates,
    portfolio, community, portals, search, notifications, team_advanced
)

# Run safe migrations
run_migrations()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    description="AI-powered Team Finder & Collaboration platform for AllCollegeEvent.com (ACE). Prototype for ACE TeamUp Challenge (International Hackathon 5.0).",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static and templates
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

# Include API Routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(events.router)
app.include_router(seats.router)
app.include_router(invites.router)
app.include_router(teams.router)
app.include_router(teams.recommended_router)
app.include_router(feedback.router)
app.include_router(safety.router)
app.include_router(icebreaker.router)
app.include_router(meta.router)
app.include_router(students.router)
app.include_router(join_requests.router)
app.include_router(opportunities.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(applications.router)
app.include_router(learn.router)
app.include_router(certificates.router)
app.include_router(portfolio.router)
app.include_router(community.router)
app.include_router(portals.router)
app.include_router(search.router)
app.include_router(notifications.router)
app.include_router(team_advanced.router)

@app.get("/api/config")
def get_app_config():
    """Returns application configuration and active matcher engine information."""
    return {
        "app_name": APP_NAME,
        "tagline": APP_TAGLINE,
        "matcher": MATCHER_TYPE,
        "ml_model_exists": (BASE_DIR / "models" / "modules.json").exists() or (BASE_DIR / "models" / "ace_teamup_model_v2").exists()
    }

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.get("/verify/{unique_id}", response_class=HTMLResponse)
@app.get("/u/{username}", response_class=HTMLResponse)
async def serve_index(request: Request, unique_id: str = None, username: str = None):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": APP_NAME,
            "tagline": APP_TAGLINE,
            "matcher": MATCHER_TYPE,
            "verify_id": unique_id,
            "portfolio_username": username
        }
    )
