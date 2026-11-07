# 🚀 AllCollegeEvent (ACE) TeamUp Platform
### The Unified AI-Powered Student Opportunity, Team Formation & Career Platform
*Prototype & Moat for the ACE TeamUp Challenge (International Hackathon 5.0)*

---

## 🌟 Vision & Platform Scope
ACE TeamUp transforms AllCollegeEvent.com into a **comprehensive one-stop student ecosystem**. A student never needs Unstop, Naukri Campus, LinkedIn, or chaotic WhatsApp groups again:
- **Opportunities Hub**: Parity with Unstop across all 16 categories (Hackathons, Quizzes, Workshops, Case Studies, Scholarships, Fellowships).
- **Jobs & Early-Career Portal**: Direct hiring from 15 verified enterprises with 1-click apply, resume builder, and skill match scoring.
- **Learn & Assessment Academy**: 40+ courses aligned with the dataset skills, 25 skill assessments awarding verified Level 1–5 badges, and 6 career learning tracks.
- **Digital Portfolio & Public Verification**: Shareable `/u/{username}` portfolio and cryptographically verifiable `/verify/{id}` credentials with QR codes.
- **Community & Mentorship**: 30 verified industry mentors with 1:1 slot booking, 40 alumni for job referrals, and collegiate campus clubs.
- **17 Unique TeamUp Innovations**: Complementary skill matching, "What If I Join?" simulator, skill gap heatmaps, 24-hr trial sprints, backup bench, and private team rooms.

---

## 🔑 Demo Accounts for Every Role

The platform supports **role-based accounts** with dedicated dashboards. You can switch between any role with 1 tap from the **"Role: Switch"** menu in the top navigation bar, or log in with these credentials:

| Role | Name & Title | Email | Password | Dashboard Features |
|---|---|---|---|---|
| **Student** | Aarav Sharma (3rd Year CSE, MAIT) | `demo@mait.ac.in` | `demo1234` | Full flow: Opps, Jobs, Resume Builder, My Space, Skill Assessments, Team Finder |
| **Organizer** | Dr. Rajesh Verma (Convenor, DTU) | `organizer@delhitechexpo.edu` | `demo1234` | Host opportunities, applicant review pipeline, team formation stats |
| **Recruiter** | Pooja Mehra (Talent Lead, Nexus Labs) | `recruiter@nexuslabs.com` | `demo1234` | Active job postings, candidate pipeline, **Talent Search over 1,050 students** |
| **Mentor** | Vikram Malhotra (Sr. AI Architect) | `mentor@aiimsalumni.ac.in` | `demo1234` | Mentorship sessions, student guidance, hackathon advice |
| **Super Admin** | ACE Administrator | `admin@allcollegeevent.com` | `admin1234` | Global telemetry, verification requests, content governance |

---

## ⚡ Quick Start & Run Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations & Seeding (Pre-seeded with 1,054 students & 305 teams)
```bash
python seed_expansion.py
```

### 3. Launch the Server
```bash
python run.py
```
Open **`http://localhost:8000`** in your browser!

- **Web Application**: `http://localhost:8000`
- **Swagger Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Interactive Docs**: `http://localhost:8000/redoc`
- **Public Certificate Verification**: `http://localhost:8000/verify/ACE-CERT-2026-F891`
- **Public Digital Portfolio**: `http://localhost:8000/u/aaravsharma`

---

## 🧪 Automated Test Verification

Run the full platform test suite:
```bash
# 1. Platform Expansion Suite (Phases 1 - 8)
python test_expansion.py

# 2. Core Matcher & Regression Suite
python test_app.py
```
Both suites pass with **100% success** across all endpoints.

---

## 🗺️ Feature Map by Phase

### Phase 1: Opportunities Hub
- **Unified `Opportunity` Model** supporting 16 categories: *Hackathon, Competition, Quiz, Case Study, Coding Challenge, Workshop, Webinar, Conference, Scholarship, Fellowship, Internship, Full-time Job, Part-time Job, Freelance Project, Mentorship Program, Campus Ambassador Role*.
- Detailed pages with eligibility, prizes, countdown timers, stages/rounds, FAQs, and instant registration.
- **Teammate Finder Bridge**: 1-click bridge from any hackathon opportunity directly to complement-based matching.

### Phase 2: Jobs & Internships Portal
- 15 verified company profiles with culture, perks, and active openings.
- 40+ job & internship listings with salary/stipend filters, work modes, and selection stages.
- **Skill-Based Recommendations**: Mathematical comparison of student proficiencies vs job requirements, explaining why it was recommended and identifying missing skills.
- **Resume Builder**: 3 templates (*Modern, Minimal, Technical*), auto-fills from student profile, exportable to PDF, and supports multiple versions with a default selection.
- **Job Alerts**: Configurable alerts notifying students when matching roles appear.

### Phase 3: My Applications & Tracking
- **My Space Tracking**: Real-time status pipeline (*Applied -> Under Review -> Shortlisted -> Interview -> Selected / Rejected / Withdrawn*).
- Status timeline history with notes and interview dates.
- Profile completeness progress meter.
- Saved bookmarks for opportunities, jobs, and courses.

### Phase 4: Learn: Courses & Skill Assessments
- **Course Catalog**: 40+ courses spanning the 31 skills from the real dataset.
- Module player with lessons, progress tracking, and knowledge quizzes.
- **Skill Assessments**: 25 standardized benchmarks awarding Level 1–5 badges with instant certificate generation upon scoring 70%+.
- **6 Curated Learning Paths**: Full Stack Developer, Machine Learning Engineer, Data Science Specialist, Cloud & DevOps, UI/UX Designer, and Cybersecurity Defense.
- **Learn-to-Qualify Engine**: Analyzes a team's minimum required skill levels, detects where the student falls short, and outputs a 1-click course pathway to bridge the gap.

### Phase 5: Certificates & Digital Portfolio
- **Verifiable Credentials**: Auto-generated for course completions, hackathon wins, and passed assessments with unique credential IDs and QR codes.
- **Public Verification**: `/verify/{id}` endpoint and public card verifying issuer, holder, issue date, and authentic status.
- **Digital Portfolio (`/u/{username}`)**: Public showcase with verified skills, reliability ratings, peer review tags, hackathon team history, and downloadable PDF summary.
- **Verified Skills**: Attach GitHub repositories, demo links, or assessment proofs to display a green "Verified" badge.

### Phase 6: Community & Career Support
- **Mentor Directory**: 30 verified senior practitioners with 1:1 slot booking.
- **Alumni Network**: 40 verified graduates open to submitting internal job referrals.
- **Technical Q&A Forums**: Opportunity-specific and skill-based discussion threads with upvotes and accepted answers.
- **Campus Colleges & Clubs**: 10 top institutions and 15 student clubs (GDSC, ACM, E-Cell, AI Societies).
- **Project Submissions**: Hackathon project submission portal (repos, live demos) with multi-criteria judging scores.

### Phase 7: Role Portals (Organizer, Recruiter, Admin)
- **Organizer Dashboard**: Host opportunities, view registrations, monitor the team formation funnel, and review applicants.
- **Recruiter Portal**: Manage job postings, review applicant pipelines, and access **Talent Search over 1,050 students** filtered by verified skills, college, and certificates.
- **Admin Dashboard**: System telemetry, verification requests, content moderation, and user management.

### Phase 8: 17 Unique TeamUp Capabilities
1. **Complement-Based Matching**: Rewards candidate skills that cover event gaps.
2. **Team Skill-Gap Heatmap**: Current levels vs requirements; missing skills glow red.
3. **"What If I Join?" Simulator**: Live mathematical before-vs-after preview of team coverage and capability boost.
4. **Learn-to-Qualify Engine**: Closing skill gaps before applying.
5. **Role-Slot Matching**: Hiring for specific open seats.
6. **Team Balance Score**: Alerts when teams lack frontend, backend, or design.
7. **Reliability Score (0-100)**: Peer-rated accountability after each event.
8. **24-Hour Trial Sprint**: Low-friction mini-task evaluation before team lock-in.
9. **Backup Bench Shortlist**: Ranked fallback roster for quick replacement.
10. **Schedule Overlap Matrix**: Synchronizing sprint hours across availabilities.
11. **Work-Style Health Check**: Telemetry from collaboration preferences.
12. **AI Pitch & Role Split**: Auto-generated 60-second pitch hook and responsibilities.
13. **Private Team Room**: Real-time team chat and Kanban task checklist.
14. **Team Reuse**: Recommending next opportunities for finished squads.
15. **Cross-College Open Seats**: Instant applications across 24 universities.
16. **Beginner-Mentor Mode**: Safe onboarding with senior alumni guidance.
17. **Explainable AI Transparency**: Mathematical justification on every card.

---

## ☁️ Deployment

- **Render Blueprint**: Pre-configured `render.yaml` and `Procfile` ready for zero-downtime deployment.
- **Vercel Serverless**: Configured `vercel.json` and `api/index.py` with automatic `/tmp` SQLite mirroring.
- **GitHub Repository**: [https://github.com/furydarkknight/teamup-ace.git](https://github.com/furydarkknight/teamup-ace.git)
