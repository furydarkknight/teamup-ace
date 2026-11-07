import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "TeamUp by ACE")
APP_TAGLINE = os.getenv("APP_TAGLINE", "AI-Powered Team Finder & Collaboration Platform for Hackathons")
SECRET_KEY = os.getenv("SECRET_KEY", "teamup-secret-jwt-key-2026-hackathon-ace")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

if os.getenv("VERCEL"):
    import shutil
    tmp_db = Path("/tmp/teamup.db")
    src_db = BASE_DIR / "teamup.db"
    if src_db.exists() and not tmp_db.exists():
        try:
            shutil.copyfile(src_db, tmp_db)
            print("[Vercel] Successfully copied teamup.db to /tmp/teamup.db")
        except Exception as e:
            print(f"[Vercel] Warning copying teamup.db to /tmp: {e}")
    DATABASE_URL = f"sqlite:///{tmp_db}"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'teamup.db'}")

MATCHER_TYPE = os.getenv("MATCHER", "rule_based").lower()  # "rule_based" or "ml"

# Verified email domains
VERIFIED_DOMAINS = (".edu", ".ac.in", ".edu.in")

# Import all categories
from app.config.categories import (
    SKILLS,
    SKILL_GROUPS,
    PROFICIENCY_LEVELS,
    PROFICIENCY_LABELS,
    INTERESTS,
    EXPERIENCE_LEVELS,
    AVAILABILITY_OPTIONS,
    PREFERRED_TEAM_SIZES,
    PREFERRED_ROLES,
    COLLABORATION_PREFERENCES,
    COLLEGES
)

# Aliases for backward compatibility
PREDEFINED_SKILLS = SKILLS
PREDEFINED_INTERESTS = INTERESTS
GOAL_OPTIONS = ["Win Grand Prize", "Learn & Build Skills", "Network & Have Fun"]
WORK_STYLES = {
    "schedule": ["Full-time", "Part-time", "Weekends"],
    "role_pref": PREFERRED_ROLES,
    "vibe": ["Competitive / Serious", "Balanced", "Casual / Experimental"]
}
