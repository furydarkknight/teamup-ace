# 🚀 TeamUp by ACE
### AI-Powered Team Finder & Collaboration Platform for AllCollegeEvent.com (ACE)
*Built for the ACE TeamUp Challenge (International Hackathon 5.0)*

---

## 📌 Problem Statement
Students struggle to find teammates with complementary skills for hackathons. Existing platforms (Unstop, Naukri Campus) are primarily event and job boards; actual team formation is relegated to chaotic WhatsApp groups and manual cold outreach, resulting in:
- **No skill-complement matching**: Teams end up with 3 backend devs and zero designers.
- **Zero reliability signal**: High ghosting rates during 36-hour sprint crunches.
- **Siloed discovery**: Limited to a student's immediate batch or campus.

**TeamUp** makes intelligent, complement-based team formation the core product.

---

## 🛠️ Tech Stack
- **Backend**: Python 3.12 with **FastAPI** (REST JSON APIs, Pydantic schemas)
- **Database**: SQLite with **SQLAlchemy ORM** (safe migrations with `app/migrations.py`)
- **Frontend**: HTML5, **Tailwind CSS** (CDN), FontAwesome 6, and responsive Vanilla JavaScript
- **Matching Engine**: Modular, swappable architecture (`matching/base.py`, `matching/rule_based.py`, `matching/ml_matcher.py`)
- **Machine Learning Support**: 229-dimensional feature schema (`models/feature_schema.json`), Sentence-Transformers embedding support (`models/ace_teamup_model_v2`), and dataset exporter (`training/export_dataset.py`)
- **Real Dataset Ready**: Seeded and imported with 1,000 real students and 300 hackathon teams (`import_data.py`)

---

## ⚡ Quick Start (One Command)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Import Real Datasets & Run Server
```bash
python import_data.py --students students.csv --teams teams.csv
python run.py
```
Open your browser at **`http://localhost:8000`**!

- **Swagger API Docs**: `http://localhost:8000/docs`
- **ReDoc Interactive Docs**: `http://localhost:8000/redoc`
- **Meta Categories API**: `http://localhost:8000/api/meta/categories`

---

## 🔑 Demo Account
An instant demo account is provided with 50 seeded students across 10 colleges:
- **Email**: `demo@mait.ac.in`
- **Password**: `demo1234`
- **User**: Aarav Sharma (3rd Year CSE, MAIT Delhi)
- **Badge**: Verified College Student (`.ac.in`)
- **Reliability Score**: 94/100 ⭐
- *(Or click the **"⚡ Instant Demo"** button on the navbar for 1-click access!)*

---

## 🎯 Key Demo Flow (End-to-End Walkthrough)

1. **Sign In**: Click **"Instant Demo"** or sign in as `demo@mait.ac.in` / `demo1234`.
2. **Open an Event**: In the Hackathons directory, open **"ACE International Hackathon 5.0"**.
3. **AI Match Feed**:
   - Notice the AI-ranked candidate cards with match percentages (e.g. 96% match).
   - Read the **explainable reasons**: e.g., *"Covers UI/UX Design & PPT/Pitching which your profile lacks for this event. Both available on Weekends with shared goal to Win Grand Prize."*
   - Filter by college (e.g., IIT Bombay, DTU), city, skills, or mentor-only.
4. **10-Minute Icebreaker Challenge**:
   - Click **"10-Min Icebreaker"** on any match card.
   - Explore the collaborative mini-task prompt, work-style breakdown (schedule & role synergy), live 10:00 countdown timer, and scratchpad.
5. **Invite a Teammate**: Click **"Invite to Team"**, propose a role, and send an invitation.
6. **Open Team Dashboard**:
   - Click **"My Teams"** in the navbar or open **"FinVision Alpha"**.
   - **Team Gap Analyzer**:
     - See live comparison of team coverage vs event requirements:
     - Identifies: `Covered: Backend, Machine Learning` vs `MISSING: UI/UX Design, PPT/Pitching`.
     - Suggests top candidates to immediately bridge each gap with a 1-click **"Invite"** button!
   - **AI-Generated Team Pitch**: Read the 60-second pitch hook tailored to the squad's skillset.
   - **Suggested Division of Labor**: View optimal role assignments for the 36-hour sprint.
7. **Team Collaboration**:
   - Send live messages in the **In-App Team Chat**.
   - Review or post **Open Seats** for the team.
   - Submit **Peer Feedback** (1-5 stars + tags like "Reliable", "Technical wizard") to update teammate Reliability Scores!

---

## 🧠 Modular Matching Engine Architecture

The matching layer is modular, bidirectional, and swappable in `matching/`:

```
matching/
├── __init__.py       # Factory pattern: get_matcher()
├── base.py           # Abstract BaseMatcher class & MatchResult dataclass
├── weights.py        # Configurable scoring weights
├── features.py       # 229-dimensional feature vector builder
├── rule_based.py     # Default complement-based weighted algorithm
└── ml_matcher.py     # Sentence-Transformers & sklearn model loader with fallback
```

### 1. Dual-Direction Matching
- **Student → Teams (`/api/me/recommended-teams`)**: Recommends open teams to a student, ranking by how well the student bridges the team's missing skill requirements and matches their working style.
- **Team → Students (`/api/teams/{id}/recommended-students`)**: Recommends students to team leads who cover flagged skill gaps.
- **Event Candidate Feed (`/api/events/{id}/matches`)**: Legacy event-based candidate discovery.

### 2. Weighted Scoring Configuration (`matching/weights.py`)
- **Skill-Gap Coverage (35%)**: Compares student proficiency against team's minimum required levels (`skill_requirements`).
- **Interest Overlap (15%)**: Jaccard similarity across 31 domain interests.
- **Role Fit (15%)**: Matches student's preferred roles with roles the team is actively hiring for.
- **Experience Fit (10%)**: Exact match (1.0), adjacent level (0.5), or different (0.1).
- **Availability Match (10%)**: Full-time, Part-time, Weekends compatibility.
- **Collaboration Style (10%)**: Matches among 10 distinct working preferences from the dataset.
- **Team Size Fit (5%)**: Evaluates preferred team size (2-8) vs team total capacity.

### 3. Switching Between Matchers (`.env`)
In your `.env` file:
```env
# Use rule-based complement matcher (default):
MATCHER=rule_based

# Or switch to ML model:
MATCHER=ml
```

### 4. 229-Feature Machine Learning Schema (`models/feature_schema.json`)
The feature builder in `matching/features.py` produces the exact 229 numerical features defined in `models/feature_schema.json`:
- 31 student skill proficiency levels (0-5)
- 31 team skill requirement minimum levels (0-5)
- 31 skill gap indicators `max(0, required - current)`
- 31 student multi-hot interest indicators
- 31 team multi-hot interest indicators
- 21 student preferred role multi-hot indicators
- 21 team preferred role multi-hot indicators
- 2 experience ordinals
- 6 availability one-hot indicators
- 20 collaboration preference one-hot indicators
- 4 team size scalars

Export pairs and train an ML model:
```bash
python training/export_dataset.py
python training/train_dummy_model.py
```

---

## 🔒 Safety & Student Verification
- **Verified Student Badge**: Automatically verified for emails ending in `.edu`, `.ac.in`, or `.edu.in`.
- **Team Creation Guard**: Only verified students can create and lead teams (unverified students can browse and apply).
- **Privacy Protection**: Phone numbers and private emails are never exposed publicly.
- **Reporting & Blocking**: Confidential reporting pipeline and 1-tap user blocking that removes users from the AI match feed.

---

## 📡 REST API Summary
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/signup` | Student registration with automatic college verification |
| `POST` | `/api/auth/login` | Login and receive JWT access token |
| `GET` | `/api/auth/me` | Fetch authenticated student profile |
| `GET/PUT` | `/api/profile` | View and update skills, work styles, and mentor flags |
| `GET` | `/api/events` | List all hackathons with filter and search |
| `GET` | `/api/events/{id}` | Hackathon event details and required roles |
| `GET` | `/api/events/{id}/matches` | **AI Match Feed**: Ranked complement-based matches with explanations |
| `GET` | `/api/events/{id}/seats` | Open seats board for an event |
| `POST` | `/api/seats` | Post an open seat for a team (Verified lead only) |
| `POST` | `/api/seats/{id}/apply` | 1-tap apply to join an open seat |
| `GET` | `/api/teams/{id}` | Team detail and members |
| `GET` | `/api/teams/{id}/gaps` | **Team Gap Analyzer**: missing roles and suggested candidates |
| `GET/POST`| `/api/teams/{id}/messages` | In-app team chat |
| `POST` | `/api/invites` | Send teammate invitation |
| `PUT` | `/api/invites/{id}` | Accept or decline team invitation |
| `POST` | `/api/feedback` | Post-event peer feedback and reliability update |
| `POST` | `/api/report` | Report user confidentially |
| `POST` | `/api/block` | Block user from match feed |
| `GET` | `/api/icebreaker/{user_id}` | 10-minute collaborative icebreaker challenge & work-style breakdown |

---

## 🏆 Prototype for ACE International Hackathon 5.0
Developed for **AllCollegeEvent.com**. Branding and configuration can be customized in `app/config.py`.
