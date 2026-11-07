import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = os.getenv("APP_NAME", "TeamUp by ACE")
APP_TAGLINE = os.getenv("APP_TAGLINE", "AI-Powered Team Finder & Collaboration Platform for Hackathons")
SECRET_KEY = os.getenv("SECRET_KEY", "teamup-secret-jwt-key-2026-hackathon-ace")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'teamup.db'}")
MATCHER_TYPE = os.getenv("MATCHER", "rule_based").lower()  # "rule_based" or "ml"

# Verified email domains
VERIFIED_DOMAINS = (".edu", ".ac.in", ".edu.in")

# Predefined Skill choices
PREDEFINED_SKILLS = [
    "Python", "C++", "Java", "JavaScript", "TypeScript", "React", "Next.js",
    "UI/UX Design", "Machine Learning", "Deep Learning", "Data Analysis",
    "Backend (Node/Python/Go)", "Frontend (HTML/CSS/JS)", "App Dev (Flutter/React Native/Swift)",
    "PPT/Pitching", "Research & Documentation", "Cybersecurity", "Cloud & DevOps (AWS/Docker)",
    "Blockchain & Web3", "Product Management"
]

PROFICIENCY_LEVELS = ["Beginner", "Intermediate", "Advanced"]

PREDEFINED_INTERESTS = [
    "AI & ML", "FinTech", "HealthTech", "Web3 & Crypto", "EdTech", 
    "ClimateTech & Sustainability", "Smart Cities & IoT", "CyberSecurity", 
    "Open Innovation", "E-Commerce", "AR/VR & Gaming"
]

AVAILABILITY_OPTIONS = ["Weekdays", "Weekends", "Evenings", "Full-time / Flexible"]

GOAL_OPTIONS = ["Win Grand Prize", "Learn & Build Skills", "Network & Have Fun"]

WORK_STYLES = {
    "schedule": ["Early Bird", "Night Owl", "Flexible"],
    "role_pref": ["Leader / Coordinator", "Executor / Builder", "Strategist / Ideator"],
    "vibe": ["Competitive / Serious", "Balanced", "Casual / Experimental"]
}
