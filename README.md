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
- **Database**: SQLite with **SQLAlchemy ORM**
- **Frontend**: HTML5, **Tailwind CSS** (CDN), FontAwesome 6, and clean Vanilla JavaScript (no heavy node frameworks)
- **Matching Engine**: Modular, swappable architecture (`matching/base.py`, `matching/rule_based.py`, `matching/ml_matcher.py`)
- **Machine Learning Support**: Feature vector extraction, training dataset export (`training/export_dataset.py`), and model runner

---

## ⚡ Quick Start (One Command)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Database & Run Server
```bash
python seed.py && python run.py
```
Open your browser at **`http://localhost:8000`**!

- **Swagger API Docs**: `http://localhost:8000/docs`
- **ReDoc Interactive Docs**: `http://localhost:8000/redoc`

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

The matching layer is swappable and decoupled in `matching/`:

```
matching/
├── __init__.py       # Factory pattern: get_matcher()
├── base.py           # Abstract BaseMatcher class & MatchResult dataclass
├── rule_based.py     # Default complement-based weighted algorithm
└── ml_matcher.py     # ML model loader with fallback & feature vector extractor
```

### 1. Weighted Scoring Algorithm (`matching/rule_based.py`)
- **Complementary Skills (40%)**: Rewards candidates who cover the specific roles the user lacks relative to the event's required roles.
- **Availability Overlap (20%)**: Compatible sprint schedules (Weekends, Evenings, Flexible).
- **Experience & Mentor Synergy (15%)**: Balanced senior-intermediate execution or beginner-mentor pairing.
- **Goal Alignment (15%)**: "Win Grand Prize" vs "Learn & Build Skills".
- **Work-Style Compatibility (10%)**: Leader-to-executor synergy, sprint pacing, and team culture vibe.

### 2. Switching Between Matchers (`.env`)
In your `.env` file:
```env
# Use rule-based complement matcher:
MATCHER=rule_based

# Or switch to trained Machine Learning model:
MATCHER=ml
```

### 3. How to Plug in Your Trained ML Model
1. **Export the Dataset**:
   ```bash
   python training/export_dataset.py
   ```
   Generates `training/teamup_match_dataset.csv` with 87 numerical feature columns and a target label `label_successful_team`.

2. **Feature Vector Format**:
   The `MLMatcher.extract_feature_vector(user, candidate, event)` produces:
   - `user_skills` (binary vector of length `len(PREDEFINED_SKILLS)`)
   - `cand_skills` (binary vector of length `len(PREDEFINED_SKILLS)`)
   - `event_roles` (binary vector of length `len(PREDEFINED_SKILLS)`)
   - `complement_skills = cand_skills * max(0, event_roles - user_skills)`
   - `availability_overlap` (float: 0.3 to 1.0)
   - `user_experience` & `cand_experience` (0=Beginner, 1=Intermediate, 2=Advanced)
   - `goal_alignment` (float: 0.4 to 1.0)
   - `workstyle_schedule_match` & `workstyle_role_synergy` (floats: 0.5 to 1.0)
   - `cand_reliability_score` (float: 0.0 to 1.0)

3. **Train and Save Model**:
   Save your trained model artifact to `models/matcher.pkl`:
   ```bash
   python training/train_dummy_model.py
   ```
   If `models/matcher.pkl` exists and `MATCHER=ml`, `MLMatcher` automatically loads and scores candidates with neural / forest predictions!

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
