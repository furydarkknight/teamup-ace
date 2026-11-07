import argparse
import json
import os
import random
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
from app.database import engine, SessionLocal, Base
from app.migrations import run_migrations
from app.models import User, Team, TeamMember, Event, OpenSeat, Invite, TeamMessage, Feedback
from app.auth import hash_password
from app.config.categories import (
    SKILLS, SKILL_GROUPS, INTERESTS, EXPERIENCE_LEVELS,
    AVAILABILITY_OPTIONS, PREFERRED_ROLES, COLLABORATION_PREFERENCES,
    COLLEGES
)

DEFAULT_STUDENTS_CSV = r"c:\Users\admin\Downloads\students.csv"
DEFAULT_TEAMS_CSV = r"c:\Users\admin\Downloads\teams.csv"

def seed_events_if_needed(db):
    """Ensures the 8 hackathon events exist with roles from the verified categories."""
    if db.query(Event).count() >= 8:
        return

    print("Creating 8 realistic hackathon events...")
    events_data = [
        {
            "name": "ACE International Hackathon 5.0",
            "tagline": "The premier flagship hackathon hosted by AllCollegeEvent.com",
            "theme": "FinTech & Open Innovation",
            "dates": "Nov 20 - Nov 22, 2026",
            "mode": "Hybrid",
            "city_venue": "MAIT Delhi Campus & Global Virtual",
            "team_size_min": 2,
            "team_size_max": 4,
            "prize_pool": "₹5,00,000",
            "description": "The flagship 36-hour hackathon challenging students to build next-generation applications in FinTech, algorithmic finance, micro-credit protocols, and open innovation. Judged by global engineering leaders.",
            "required_roles": ["Machine Learning Engineer", "Backend Developer", "UI/UX Designer", "Presenter/Communicator"],
            "banner_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "HealthHack Global 2026",
            "tagline": "AI and smart diagnostics for preventive healthcare",
            "theme": "HealthTech",
            "dates": "Dec 05 - Dec 07, 2026",
            "mode": "Online",
            "city_venue": "Virtual",
            "team_size_min": 2,
            "team_size_max": 4,
            "prize_pool": "₹2,50,000",
            "description": "Design accessible healthcare solutions, clinical predictive modeling, and telehealth applications for underserved communities.",
            "required_roles": ["Machine Learning Engineer", "Frontend Developer", "UI/UX Designer", "Research Lead"],
            "banner_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "Web3 Nexus Sprint",
            "tagline": "Decentralized protocols, smart contracts, and tokenomics",
            "theme": "Web3 & Crypto",
            "dates": "Dec 12 - Dec 14, 2026",
            "mode": "Hybrid",
            "city_venue": "Bangalore Tech Park & Online",
            "team_size_min": 2,
            "team_size_max": 4,
            "prize_pool": "₹3,00,000",
            "description": "Build decentralized applications, zero-knowledge proof identity tools, and layer-2 DeFi liquidity mechanisms.",
            "required_roles": ["Blockchain Developer", "Frontend Developer", "Backend Developer", "Cybersecurity Analyst"],
            "banner_url": "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "SmartCity IoT Challenge",
            "tagline": "Autonomous infrastructure, clean mobility, and smart grids",
            "theme": "Smart Cities & IoT",
            "dates": "Dec 18 - Dec 20, 2026",
            "mode": "In-Person",
            "city_venue": "IIT Bombay Auditorium, Mumbai",
            "team_size_min": 2,
            "team_size_max": 4,
            "prize_pool": "₹2,00,000",
            "description": "Leverage edge computing, sensor telemetry, and urban analytics to tackle traffic congestion, water supply tracking, and waste management.",
            "required_roles": ["IoT Engineer", "Cloud Engineer", "Data Analyst", "Presenter/Communicator"],
            "banner_url": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "EduNova Hack 2026",
            "tagline": "Personalized AI tutors and immersive learning spaces",
            "theme": "EdTech",
            "dates": "Jan 08 - Jan 10, 2027",
            "mode": "Online",
            "city_venue": "Virtual",
            "team_size_min": 2,
            "team_size_max": 3,
            "prize_pool": "₹1,50,000",
            "description": "Rethink classroom engagement, real-time code sandboxes, and neuro-divergent learning tools using generative AI.",
            "required_roles": ["Frontend Developer", "UI/UX Designer", "Backend Developer", "Project Manager"],
            "banner_url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "EcoTech Climate Summit",
            "tagline": "Carbon credit tracking and renewable energy optimization",
            "theme": "ClimateTech & Sustainability",
            "dates": "Jan 15 - Jan 17, 2027",
            "mode": "Online",
            "city_venue": "Virtual",
            "team_size_min": 2,
            "team_size_max": 4,
            "prize_pool": "₹2,00,000",
            "description": "Satellite imagery analytics, supply chain carbon accounting, and decentralized carbon offset verification.",
            "required_roles": ["Data Analyst", "Machine Learning Engineer", "Research Lead", "Frontend Developer"],
            "banner_url": "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "CyberShield Defenseathon",
            "tagline": "Offensive & defensive cybersecurity, zero-day threat defense",
            "theme": "CyberSecurity",
            "dates": "Jan 22 - Jan 24, 2027",
            "mode": "Online",
            "city_venue": "Virtual",
            "team_size_min": 2,
            "team_size_max": 3,
            "prize_pool": "₹3,50,000",
            "description": "Penetration testing automation, AI-driven malware detection, secure enclave hardware design, and cloud posture hardening.",
            "required_roles": ["Cybersecurity Analyst", "Cloud Engineer", "Backend Developer", "DevOps Engineer"],
            "banner_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=1200&auto=format&fit=crop&q=80"
        },
        {
            "name": "Campus Catalyst Hackfest",
            "tagline": "Solve real-world problems facing Indian college campuses",
            "theme": "Open Innovation",
            "dates": "Feb 05 - Feb 07, 2027",
            "mode": "Hybrid",
            "city_venue": "Delhi Technological University & Online",
            "team_size_min": 2,
            "team_size_max": 4,
            "prize_pool": "₹1,75,000",
            "description": "From hostel room allocations to inter-college sports analytics, build apps that make campus life seamless.",
            "required_roles": ["Full Stack Developer", "UI/UX Designer", "Presenter/Communicator", "Project Manager"],
            "banner_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=1200&auto=format&fit=crop&q=80"
        }
    ]

    for ed in events_data:
        req_roles = ed.pop("required_roles")
        e = Event(**ed)
        e.required_roles = req_roles
        db.add(e)
    db.commit()

def import_datasets(students_path: str, teams_path: str):
    print("="*65)
    print(">>> STARTING REAL DATASET IMPORT FOR TEAMUP")
    print(f">> Students CSV: {students_path}")
    print(f">> Teams CSV:    {teams_path}")
    print("="*65)

    # Run safe schema migration
    run_migrations()
    db = SessionLocal()

    # Seed events
    seed_events_if_needed(db)
    events = db.query(Event).all()
    event_ids = [e.id for e in events] if events else [1]

    # Category validation sets
    skill_set = set(SKILLS)
    interest_set = set(INTERESTS)
    exp_set = set(EXPERIENCE_LEVELS)
    avail_set = set(AVAILABILITY_OPTIONS)
    role_set = set(PREFERRED_ROLES)
    collab_set = set(COLLABORATION_PREFERENCES)

    # 1. Ensure Demo Account exists (demo@mait.ac.in)
    demo_hashed = hash_password("demo1234")
    demo_user = db.query(User).filter(User.email == "demo@mait.ac.in").first()
    if not demo_user:
        print("[+] Creating demo account (demo@mait.ac.in)...")
        demo_user = User(
            student_id="DEMO_AARAV",
            email="demo@mait.ac.in",
            hashed_password=demo_hashed,
            is_verified=True,
            name="Aarav Sharma",
            college="Maharaja Agrasen Institute of Technology (MAIT)",
            city="Delhi",
            year="3rd Year B.Tech CSE",
            bio="Full-stack engineer passionate about FinTech, distributed microservices, and AI integrations. Built 3 production web apps. Looking for ML and UI/UX designers for ACE Hackathon!",
            short_bio="Full-stack engineer passionate about FinTech and distributed systems.",
            avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=AaravSharma",
            skills_json=json.dumps(["Backend (Node/Python/Go)", "Python", "React", "SQL"]),
            skill_proficiency_json=json.dumps({"Python": 5, "React": 4, "SQL": 4, "FastAPI": 4}),
            interests_json=json.dumps(["FinTech", "Artificial Intelligence", "Analytics"]),
            experience_level="Intermediate",
            project_experience_json=json.dumps(["Engineered multi-tenant microservices for real-time payments"]),
            preferred_roles_json=json.dumps(["Full Stack Developer", "Backend Developer"]),
            availability="Full-time",
            preferred_team_size=4,
            collaboration_preference="Thrives in agile environments with daily standups",
            reliability_score=94.0,
            ratings_count=4
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)

    # 2. Import Students
    print("\n[+] Reading and validating students.csv...")
    students_df = pd.read_csv(students_path)
    print(f"    Total rows in students.csv: {len(students_df)}")

    imported_students = 0
    updated_students = 0
    skipped_students = 0

    student_id_to_user = {}

    for idx, row in students_df.iterrows():
        try:
            s_id = str(row["student_id"]).strip()
            name = str(row["name"]).strip()
            college = str(row["college"]).strip()
            
            # Parse JSON fields safely
            s_skills = json.loads(row["skills"]) if isinstance(row["skills"], str) else []
            s_prof = json.loads(row["skill_proficiency"]) if isinstance(row["skill_proficiency"], str) else {}
            s_interests = json.loads(row["interests"]) if isinstance(row["interests"], str) else []
            s_projects = json.loads(row["project_experience"]) if isinstance(row["project_experience"], str) else []
            s_roles = json.loads(row["preferred_roles"]) if isinstance(row["preferred_roles"], str) else []
            
            exp_level = str(row["experience_level"]).strip()
            if exp_level not in exp_set:
                exp_level = "Intermediate"
                
            avail = str(row["availability"]).strip()
            if avail not in avail_set:
                avail = "Full-time"
                
            team_size = int(row["preferred_team_size"]) if pd.notnull(row["preferred_team_size"]) else 4
            collab_pref = str(row["collaboration_preference"]).strip()
            bio = str(row["bio"]).strip() if pd.notnull(row["bio"]) else ""

            # Check if student exists
            existing_user = db.query(User).filter(User.student_id == s_id).first()
            user_email = f"{s_id.lower()}@demo.ac.in"

            # Reliability score based on experience
            if exp_level == "Advanced":
                rel = round(random.uniform(88.0, 99.0), 1)
                ratings = random.randint(3, 10)
            elif exp_level == "Intermediate":
                rel = round(random.uniform(78.0, 92.0), 1)
                ratings = random.randint(1, 6)
            else:
                rel = 0.0
                ratings = 0

            avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={s_id}"

            if existing_user:
                existing_user.name = name
                existing_user.college = college
                existing_user.skills = s_skills
                existing_user.skill_proficiency = s_prof
                existing_user.interests = s_interests
                existing_user.project_experience = s_projects
                existing_user.preferred_roles = s_roles
                existing_user.experience_level = exp_level
                existing_user.availability = avail
                existing_user.preferred_team_size = team_size
                existing_user.collaboration_preference = collab_pref
                existing_user.bio = bio
                existing_user.short_bio = bio[:200]
                student_id_to_user[s_id] = existing_user
                updated_students += 1
            else:
                new_user = User(
                    student_id=s_id,
                    email=user_email,
                    hashed_password=demo_hashed,
                    is_verified=True, # Auto-verify imported students
                    name=name,
                    college=college,
                    city="Delhi" if college.startswith("M") or college.startswith("D") else "Campus",
                    year="3rd Year B.Tech",
                    bio=bio,
                    short_bio=bio[:200],
                    avatar_url=avatar,
                    skills_json=json.dumps(s_skills),
                    skill_proficiency_json=json.dumps(s_prof),
                    interests_json=json.dumps(s_interests),
                    project_experience_json=json.dumps(s_projects),
                    preferred_roles_json=json.dumps(s_roles),
                    experience_level=exp_level,
                    availability=avail,
                    preferred_team_size=team_size,
                    collaboration_preference=collab_pref,
                    reliability_score=rel,
                    ratings_count=ratings
                )
                db.add(new_user)
                student_id_to_user[s_id] = new_user
                imported_students += 1

            if (idx + 1) % 200 == 0:
                db.commit()
                print(f"    Processed {idx + 1} / {len(students_df)} students...")

        except Exception as e:
            print(f"    [!] Error parsing student row {idx} (id={row.get('student_id')}): {e}")
            skipped_students += 1

    db.commit()
    print(f"[OK] Students Import Completed: {imported_students} created, {updated_students} updated, {skipped_students} skipped.")

    # Refresh map of student_id -> User
    all_users = db.query(User).all()
    for u in all_users:
        if u.student_id:
            student_id_to_user[u.student_id] = u

    # 3. Import Teams
    print("\n[+] Reading and validating teams.csv...")
    teams_df = pd.read_csv(teams_path)
    print(f"    Total rows in teams.csv: {len(teams_df)}")

    imported_teams = 0
    updated_teams = 0
    skipped_teams = 0
    missing_member_warnings = 0

    for idx, row in teams_df.iterrows():
        try:
            t_id = str(row["team_id"]).strip()
            t_name = str(row["team_name"]).strip()
            college = str(row["college"]).strip()

            current_mems = json.loads(row["current_members"]) if isinstance(row["current_members"], str) else []
            vacancies = int(row["vacancies"]) if pd.notnull(row["vacancies"]) else 1
            curr_skills = json.loads(row["current_skills"]) if isinstance(row["current_skills"], str) else {}
            req_skills = json.loads(row["required_skills"]) if isinstance(row["required_skills"], str) else []
            pref_skills = json.loads(row["preferred_skills"]) if isinstance(row["preferred_skills"], str) else []
            skill_reqs = json.loads(row["skill_requirements"]) if isinstance(row["skill_requirements"], str) else {}
            t_interests = json.loads(row["interests"]) if isinstance(row["interests"], str) else []
            
            pref_exp = str(row["preferred_experience"]).strip()
            if pref_exp not in exp_set:
                pref_exp = "Intermediate"

            avail = str(row["availability"]).strip()
            if avail not in avail_set:
                avail = "Full-time"

            pref_roles = json.loads(row["preferred_roles"]) if isinstance(row["preferred_roles"], str) else []
            t_desc = str(row["team_description"]).strip() if pd.notnull(row["team_description"]) else ""
            collab_pref = str(row["collaboration_preference"]).strip()

            # Find leader from first member in current_members
            leader_user = None
            for m_id in current_mems:
                if m_id in student_id_to_user:
                    leader_user = student_id_to_user[m_id]
                    break
                else:
                    missing_member_warnings += 1

            if not leader_user:
                leader_user = demo_user

            # Assign event evenly
            ev_id = event_ids[idx % len(event_ids)]

            existing_team = db.query(Team).filter(Team.team_id == t_id).first()

            if existing_team:
                existing_team.name = t_name
                existing_team.team_name = t_name
                existing_team.college = college
                existing_team.current_members = current_mems
                existing_team.vacancies = vacancies
                existing_team.current_skills = curr_skills
                existing_team.required_skills = req_skills
                existing_team.preferred_skills = pref_skills
                existing_team.skill_requirements = skill_reqs
                existing_team.interests = t_interests
                existing_team.preferred_experience = pref_exp
                existing_team.availability = avail
                existing_team.preferred_roles = pref_roles
                existing_team.team_description = t_desc
                existing_team.tagline = t_desc[:120] if t_desc else "Competing at ACE Hackathon"
                existing_team.collaboration_preference = collab_pref
                existing_team.leader_id = leader_user.id
                target_team = existing_team
                updated_teams += 1
            else:
                new_team = Team(
                    team_id=t_id,
                    name=t_name,
                    team_name=t_name,
                    college=college,
                    current_members_json=json.dumps(current_mems),
                    current_team_size=len(current_mems),
                    vacancies=vacancies,
                    current_skills_json=json.dumps(curr_skills),
                    required_skills_json=json.dumps(req_skills),
                    preferred_skills_json=json.dumps(pref_skills),
                    skill_requirements_json=json.dumps(skill_reqs),
                    interests_json=json.dumps(t_interests),
                    preferred_experience=pref_exp,
                    availability=avail,
                    preferred_roles_json=json.dumps(pref_roles),
                    team_description=t_desc,
                    tagline=t_desc[:120] if t_desc else "Competing at ACE Hackathon",
                    collaboration_preference=collab_pref,
                    event_id=ev_id,
                    leader_id=leader_user.id
                )
                db.add(new_team)
                target_team = new_team
                imported_teams += 1

            db.flush()

            # Ensure TeamMember records exist for current_members
            db.query(TeamMember).filter(TeamMember.team_id == target_team.id).delete()
            for m_idx, m_id in enumerate(current_mems):
                u_obj = student_id_to_user.get(m_id)
                if u_obj:
                    # Role assigned: either leader or from student preferred_roles
                    member_role = "Team Lead" if m_idx == 0 else (u_obj.preferred_roles[0] if u_obj.preferred_roles else "Core Developer")
                    tm = TeamMember(
                        team_id=target_team.id,
                        user_id=u_obj.id,
                        role=member_role
                    )
                    db.add(tm)

            if (idx + 1) % 100 == 0:
                db.commit()
                print(f"    Processed {idx + 1} / {len(teams_df)} teams...")

        except Exception as e:
            print(f"    [!] Error parsing team row {idx} (id={row.get('team_id')}): {e}")
            skipped_teams += 1

    db.commit()
    db.close()

    print("\n" + "="*65)
    print(">>> DATASET IMPORT SUMMARY REPORT:")
    print(f">> Total Students Created: {imported_students}")
    print(f">> Total Students Updated: {updated_students}")
    print(f">> Total Students Skipped: {skipped_students}")
    print(f">> Total Teams Created:    {imported_teams}")
    print(f">> Total Teams Updated:    {updated_teams}")
    print(f">> Total Teams Skipped:    {skipped_teams}")
    print(f">> Member ID Warnings:     {missing_member_warnings}")
    print("="*65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import real students and teams dataset into TeamUp by ACE")
    parser.add_argument("--students", type=str, default=DEFAULT_STUDENTS_CSV, help="Path to students.csv")
    parser.add_argument("--teams", type=str, default=DEFAULT_TEAMS_CSV, help="Path to teams.csv")
    args = parser.parse_args()

    import_datasets(args.students, args.teams)
