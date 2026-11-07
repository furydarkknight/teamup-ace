import json
import random
from pathlib import Path
import sys

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from app.database import engine, Base, SessionLocal
from app.models import User, Event, Team, TeamMember, OpenSeat, SeatApplication, Invite, TeamMessage, Feedback
from app.auth import hash_password, check_is_verified_email
from app.config import PREDEFINED_SKILLS, PREDEFINED_INTERESTS

COLLEGES = [
    ("Maharaja Agrasen Institute of Technology (MAIT)", "Delhi", ".ac.in"),
    ("IIT Bombay", "Mumbai", ".ac.in"),
    ("BITS Pilani", "Pilani", ".ac.in"),
    ("Delhi Technological University (DTU)", "Delhi", ".ac.in"),
    ("Vellore Institute of Technology (VIT)", "Vellore", ".ac.in"),
    ("RV College of Engineering (RVCE)", "Bangalore", ".edu.in"),
    ("IIIT Hyderabad", "Hyderabad", ".ac.in"),
    ("Netaji Subhas University of Technology (NSUT)", "Delhi", ".ac.in"),
    ("Punjab Engineering College (PEC)", "Chandigarh", ".edu.in"),
    ("IIT Madras", "Chennai", ".ac.in"),
]

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Ishaan", "Diya", "Kabir", "Meera",
    "Aditya", "Sneha", "Vikram", "Tanvi", "Siddharth", "Pooja", "Arjun", "Rhea",
    "Aryan", "Kavya", "Dhruv", "Isha", "Karan", "Simran", "Varun", "Nisha",
    "Yash", "Avani", "Rishabh", "Shreya", "Sameer", "Tara", "Nikhil", "Gauri",
    "Harsh", "Bhavya", "Dev", "Alia", "Pranav", "Zoya", "Rajat", "Sakshi",
    "Akash", "Tanya", "Ayush", "Manya", "Sanket", "Neha", "Utkarsh", "Swati",
    "Madhav", "Kriti"
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Singh", "Reddy", "Iyer", "Nair",
    "Mehta", "Agarwal", "Bansal", "Chopra", "Joshi", "Bhatia", "Malhotra",
    "Saxena", "Deshmukh", "Kulkarni", "Ghosh", "Chatterjee", "Mishra", "Pandey"
]

def seed_database():
    print("Initializing TeamUp database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    print("Generating 50 realistic student profiles...")
    users = []

    # 1. Create Demo Account (Aarav Sharma - MAIT Delhi)
    demo_hashed = hash_password("demo1234")
    demo_user = User(
        email="demo@mait.ac.in",
        hashed_password=demo_hashed,
        is_verified=True,
        name="Aarav Sharma",
        college="Maharaja Agrasen Institute of Technology (MAIT)",
        city="Delhi",
        year="3rd Year B.Tech CSE",
        short_bio="Full-stack engineer passionate about FinTech, distributed microservices, and AI integrations. Built 3 production web apps. Looking for ML and UI/UX designers for ACE Hackathon!",
        avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=AaravSharma",
        skills_json=json.dumps([
            {"name": "Backend (Node/Python/Go)", "level": "Advanced"},
            {"name": "Python", "level": "Advanced"},
            {"name": "Frontend (HTML/CSS/JS)", "level": "Intermediate"},
            {"name": "React", "level": "Intermediate"}
        ]),
        interests_json=json.dumps(["FinTech", "AI & ML", "Smart Cities & IoT"]),
        experience_level="Intermediate",
        past_hackathons_count=3,
        github_url="https://github.com/aaravsharma-demo",
        linkedin_url="https://linkedin.com/in/aaravsharma-demo",
        availability="Weekends",
        goal="Win Grand Prize",
        work_schedule="Night Owl",
        work_role="Leader / Coordinator",
        work_vibe="Competitive / Serious",
        is_mentor=False,
        seeking_mentor=False,
        reliability_score=94.0,
        ratings_count=4
    )
    db.add(demo_user)
    users.append(demo_user)

    # 2. Distinct candidate profiles crafted for complementary matching
    # Profile 2: Ananya Iyer (IIT Bombay) - Complementary ML & UI/UX Expert
    u2 = User(
        email="ananya.iyer@iitb.ac.in",
        hashed_password=demo_hashed,
        is_verified=True,
        name="Ananya Iyer",
        college="IIT Bombay",
        city="Mumbai",
        year="4th Year B.Tech AI",
        short_bio="Machine learning researcher & UI/UX designer. Won 1st place at HackIITB 2025. Love crafting intuitive user experiences on top of complex neural networks.",
        avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=AnanyaIyer",
        skills_json=json.dumps([
            {"name": "Machine Learning", "level": "Advanced"},
            {"name": "UI/UX Design", "level": "Advanced"},
            {"name": "Deep Learning", "level": "Advanced"},
            {"name": "PPT/Pitching", "level": "Intermediate"}
        ]),
        interests_json=json.dumps(["AI & ML", "HealthTech", "FinTech"]),
        experience_level="Advanced",
        past_hackathons_count=6,
        github_url="https://github.com/ananyaiyer",
        linkedin_url="https://linkedin.com/in/ananyaiyer",
        availability="Weekends",
        goal="Win Grand Prize",
        work_schedule="Night Owl",
        work_role="Executor / Builder",
        work_vibe="Competitive / Serious",
        is_mentor=True,
        seeking_mentor=False,
        reliability_score=97.5,
        ratings_count=8
    )
    db.add(u2)
    users.append(u2)

    # Profile 3: Rohan Gupta (DTU) - UI/UX & Pitching Wizard
    u3 = User(
        email="rohan.gupta@dtu.ac.in",
        hashed_password=demo_hashed,
        is_verified=True,
        name="Rohan Gupta",
        college="Delhi Technological University (DTU)",
        city="Delhi",
        year="3rd Year B.Des",
        short_bio="Product designer & pitch presenter. Master at Figma wireframes, motion graphics, and high-impact deck storytelling. 4 hackathon podiums.",
        avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=RohanGupta",
        skills_json=json.dumps([
            {"name": "UI/UX Design", "level": "Advanced"},
            {"name": "PPT/Pitching", "level": "Advanced"},
            {"name": "Product Management", "level": "Intermediate"},
            {"name": "Frontend (HTML/CSS/JS)", "level": "Intermediate"}
        ]),
        interests_json=json.dumps(["FinTech", "EdTech", "E-Commerce"]),
        experience_level="Intermediate",
        past_hackathons_count=4,
        github_url="https://github.com/rohangupta",
        linkedin_url="https://linkedin.com/in/rohangupta",
        availability="Weekends",
        goal="Win Grand Prize",
        work_schedule="Night Owl",
        work_role="Strategist / Ideator",
        work_vibe="Competitive / Serious",
        is_mentor=False,
        seeking_mentor=False,
        reliability_score=92.0,
        ratings_count=5
    )
    db.add(u3)
    users.append(u3)

    # Profile 4: Priya Nair (BITS Pilani) - App Dev & ML
    u4 = User(
        email="priya.nair@pilani.bits-pilani.ac.in",
        hashed_password=demo_hashed,
        is_verified=True,
        name="Priya Nair",
        college="BITS Pilani",
        city="Pilani",
        year="2nd Year B.Tech",
        short_bio="Flutter & iOS developer. Built 2 cross-platform mobile apps with 10k+ downloads. Seeking senior teammates to level up backend & AI skills.",
        avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=PriyaNair",
        skills_json=json.dumps([
            {"name": "App Dev (Flutter/React Native/Swift)", "level": "Advanced"},
            {"name": "Frontend (HTML/CSS/JS)", "level": "Intermediate"},
            {"name": "UI/UX Design", "level": "Intermediate"}
        ]),
        interests_json=json.dumps(["HealthTech", "AI & ML", "Open Innovation"]),
        experience_level="Intermediate",
        past_hackathons_count=2,
        github_url="https://github.com/priyanair",
        linkedin_url="https://linkedin.com/in/priyanair",
        availability="Full-time / Flexible",
        goal="Learn & Build Skills",
        work_schedule="Flexible",
        work_role="Executor / Builder",
        work_vibe="Balanced",
        is_mentor=False,
        seeking_mentor=True,
        reliability_score=89.0,
        ratings_count=3
    )
    db.add(u4)
    users.append(u4)

    # Profile 5: Kabir Mehta (IIIT Hyderabad) - Data Science & Research Mentor
    u5 = User(
        email="kabir.mehta@iiit.ac.in",
        hashed_password=demo_hashed,
        is_verified=True,
        name="Kabir Mehta",
        college="IIIT Hyderabad",
        city="Hyderabad",
        year="Dual Degree M.Tech",
        short_bio="NLP and Data Science specialist. Excited to mentor high-energy beginners and build scalable algorithmic backends.",
        avatar_url="https://api.dicebear.com/7.x/bottts/svg?seed=KabirMehta",
        skills_json=json.dumps([
            {"name": "Machine Learning", "level": "Advanced"},
            {"name": "Data Analysis", "level": "Advanced"},
            {"name": "Python", "level": "Advanced"},
            {"name": "Research & Documentation", "level": "Advanced"}
        ]),
        interests_json=json.dumps(["AI & ML", "FinTech", "CyberSecurity"]),
        experience_level="Advanced",
        past_hackathons_count=7,
        github_url="https://github.com/kabirmehta",
        linkedin_url="https://linkedin.com/in/kabirmehta",
        availability="Weekends",
        goal="Win Grand Prize",
        work_schedule="Early Bird",
        work_role="Leader / Coordinator",
        work_vibe="Competitive / Serious",
        is_mentor=True,
        seeking_mentor=False,
        reliability_score=98.0,
        ratings_count=9
    )
    db.add(u5)
    users.append(u5)

    # 45 Additional Diverse Profiles
    roles_pool = [
        [("UI/UX Design", "Advanced"), ("Frontend (HTML/CSS/JS)", "Intermediate"), ("PPT/Pitching", "Intermediate")],
        [("Machine Learning", "Advanced"), ("Python", "Advanced"), ("Data Analysis", "Intermediate")],
        [("Backend (Node/Python/Go)", "Advanced"), ("Cloud & DevOps (AWS/Docker)", "Intermediate"), ("Python", "Advanced")],
        [("Blockchain & Web3", "Advanced"), ("Backend (Node/Python/Go)", "Intermediate"), ("Cybersecurity", "Intermediate")],
        [("App Dev (Flutter/React Native/Swift)", "Advanced"), ("UI/UX Design", "Intermediate"), ("React", "Intermediate")],
        [("PPT/Pitching", "Advanced"), ("Product Management", "Advanced"), ("Research & Documentation", "Intermediate")],
        [("Cybersecurity", "Advanced"), ("Python", "Advanced"), ("Cloud & DevOps (AWS/Docker)", "Intermediate")],
        [("React", "Advanced"), ("Next.js", "Advanced"), ("Frontend (HTML/CSS/JS)", "Advanced")],
        [("Data Analysis", "Advanced"), ("Research & Documentation", "Advanced"), ("Python", "Intermediate")],
        [("Backend (Node/Python/Go)", "Intermediate"), ("React", "Intermediate"), ("Python", "Intermediate")]
    ]

    schedules = ["Night Owl", "Early Bird", "Flexible"]
    work_roles = ["Executor / Builder", "Leader / Coordinator", "Strategist / Ideator"]
    vibes = ["Competitive / Serious", "Balanced", "Casual / Experimental"]
    availabilities = ["Weekends", "Weekdays", "Evenings", "Full-time / Flexible"]
    goals = ["Win Grand Prize", "Learn & Build Skills", "Network & Have Fun"]
    experiences = ["Beginner", "Intermediate", "Advanced"]

    for i in range(5, 50):
        first = FIRST_NAMES[i]
        last = LAST_NAMES[i % len(LAST_NAMES)]
        name = f"{first} {last}"
        college_tuple = COLLEGES[i % len(COLLEGES)]
        col_name, city, domain_ext = college_tuple

        # Mix verified and non-verified (80% verified with college emails)
        if i % 6 == 0:
            email = f"{first.lower()}.{last.lower()}{i}@gmail.com"
            is_verified = False
        else:
            email = f"{first.lower()}.{last.lower()}@{col_name.lower().split()[0]}{domain_ext}"
            is_verified = True

        selected_skills = random.choice(roles_pool)
        skills_data = [{"name": s[0], "level": s[1]} for s in selected_skills]
        # Maybe add a secondary skill
        if random.random() > 0.5:
            extra = random.choice(PREDEFINED_SKILLS)
            if not any(s["name"] == extra for s in skills_data):
                skills_data.append({"name": extra, "level": "Intermediate"})

        interests = random.sample(PREDEFINED_INTERESTS, k=random.randint(2, 4))
        exp = random.choice(experiences)
        past_count = random.randint(0, 5) if exp != "Advanced" else random.randint(3, 8)
        
        # Reliability score
        if past_count == 0:
            rel_score = 0.0 # New member
            rat_count = 0
        else:
            rel_score = round(random.uniform(78.0, 99.0), 1)
            rat_count = random.randint(2, 10)

        is_mentor = True if (exp == "Advanced" and i % 3 == 0) else False
        seeking_mentor = True if (exp == "Beginner" and i % 2 == 0) else False

        user = User(
            email=email,
            hashed_password=demo_hashed,
            is_verified=is_verified,
            name=name,
            college=col_name,
            city=city,
            year=f"{random.randint(1, 4)}th Year B.Tech",
            short_bio=f"{exp} developer from {col_name}. Focused on {', '.join(interests[:2])}. Eager to collaborate and create impact!",
            avatar_url=f"https://api.dicebear.com/7.x/bottts/svg?seed={first}{last}",
            skills_json=json.dumps(skills_data),
            interests_json=json.dumps(interests),
            experience_level=exp,
            past_hackathons_count=past_count,
            github_url=f"https://github.com/{first.lower()}-{last.lower()}",
            linkedin_url=f"https://linkedin.com/in/{first.lower()}-{last.lower()}",
            availability=random.choice(availabilities),
            goal=random.choice(goals),
            work_schedule=random.choice(schedules),
            work_role=random.choice(work_roles),
            work_vibe=random.choice(vibes),
            is_mentor=is_mentor,
            seeking_mentor=seeking_mentor,
            reliability_score=rel_score,
            ratings_count=rat_count
        )
        db.add(user)
        users.append(user)

    db.commit()
    print(f"[OK] Created {len(users)} user profiles.")

    # 3. Create 8 Hackathon Events
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
            "required_roles": ["Machine Learning", "Backend (Node/Python/Go)", "UI/UX Design", "PPT/Pitching"],
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
            "required_roles": ["Machine Learning", "App Dev (Flutter/React Native/Swift)", "UI/UX Design", "Research & Documentation"],
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
            "required_roles": ["Blockchain & Web3", "Frontend (HTML/CSS/JS)", "Backend (Node/Python/Go)", "Cybersecurity"],
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
            "required_roles": ["Python", "Cloud & DevOps (AWS/Docker)", "Data Analysis", "PPT/Pitching"],
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
            "required_roles": ["React", "UI/UX Design", "Backend (Node/Python/Go)", "Product Management"],
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
            "required_roles": ["Data Analysis", "Machine Learning", "Research & Documentation", "Frontend (HTML/CSS/JS)"],
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
            "required_roles": ["Cybersecurity", "Python", "Backend (Node/Python/Go)", "Cloud & DevOps (AWS/Docker)"],
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
            "required_roles": ["App Dev (Flutter/React Native/Swift)", "UI/UX Design", "Frontend (HTML/CSS/JS)", "PPT/Pitching"],
            "banner_url": "https://images.unsplash.com/photo-1523240795612-9a054b0db644?w=1200&auto=format&fit=crop&q=80"
        }
    ]

    events = []
    for ed in events_data:
        req_roles = ed.pop("required_roles")
        e = Event(**ed)
        e.required_roles = req_roles
        db.add(e)
        events.append(e)

    db.commit()
    print(f"[OK] Created {len(events)} hackathon events.")

    # 4. Create 5 Existing Teams
    print("Creating 5 existing teams...")
    # Team 1: Demo user leads team for ACE Hackathon
    team1 = Team(
        event_id=events[0].id,
        name="FinVision Alpha",
        tagline="Next-gen AI lending infrastructure for MSMEs",
        leader_id=demo_user.id,
        pitch="FinVision Alpha combines real-time transaction underwriting with a seamless mobile credit pipeline to empower micro-merchants."
    )
    db.add(team1)
    db.flush()

    # Aarav is lead & backend
    db.add(TeamMember(team_id=team1.id, user_id=demo_user.id, role="Backend & Architecture Lead"))
    # Member 2: Ananya Iyer (ML expert)
    db.add(TeamMember(team_id=team1.id, user_id=u2.id, role="Lead ML Engineer"))
    # Notice: Team1 has Backend and ML, but lacks UI/UX and PPT/Pitching!
    # This provides a realistic demonstration for the Team Gap Analyzer!

    # Team 2: HealthAI Labs (HealthHack)
    team2 = Team(
        event_id=events[1].id,
        name="NeuroPulse",
        tagline="Non-invasive stroke detection via smartphone telemetry",
        leader_id=u5.id, # Kabir Mehta
        pitch="NeuroPulse deploys on-device neural nets to detect early motor impairment in seconds."
    )
    db.add(team2)
    db.flush()
    db.add(TeamMember(team_id=team2.id, user_id=u5.id, role="Algorithm Lead"))
    db.add(TeamMember(team_id=team2.id, user_id=u4.id, role="Mobile App Developer"))

    # Team 3: BlockSentry (Web3 Nexus)
    team3 = Team(
        event_id=events[2].id,
        name="ZeroVault",
        tagline="Zero-knowledge private payroll on Ethereum",
        leader_id=users[6].id,
        pitch="ZeroVault enables corporations to stream salaries without disclosing compensation amounts on public ledgers."
    )
    db.add(team3)
    db.flush()
    db.add(TeamMember(team_id=team3.id, user_id=users[6].id, role="Smart Contract Lead"))
    db.add(TeamMember(team_id=team3.id, user_id=users[7].id, role="Frontend Web3 Engineer"))

    # Team 4: UrbanSync (SmartCity Challenge)
    team4 = Team(
        event_id=events[3].id,
        name="GridWise",
        tagline="Dynamic street light load balancing with solar storage",
        leader_id=users[9].id,
        pitch="GridWise cuts municipal power consumption by 40% with adaptive sensor routing."
    )
    db.add(team4)
    db.flush()
    db.add(TeamMember(team_id=team4.id, user_id=users[9].id, role="Hardware & Cloud Lead"))
    db.add(TeamMember(team_id=team4.id, user_id=users[10].id, role="Data Scientist"))

    # Team 5: EduMatrix (EduNova Hack)
    team5 = Team(
        event_id=events[4].id,
        name="LearnSphere",
        tagline="Gamified peer code review and live debugging arena",
        leader_id=users[12].id,
        pitch="LearnSphere turns technical problem sets into multiplayer cooperative quests."
    )
    db.add(team5)
    db.flush()
    db.add(TeamMember(team_id=team5.id, user_id=users[12].id, role="Frontend Engineer"))
    db.add(TeamMember(team_id=team5.id, user_id=users[13].id, role="Full-Stack Dev"))

    db.commit()
    print("[OK] Created 5 existing teams.")

    # 5. Create 6 Open Seats
    print("Creating 6 open seat postings...")
    seats_data = [
        {
            "team_id": team1.id,
            "event_id": events[0].id,
            "role_title": "Lead UI/UX Designer",
            "required_skills": ["UI/UX Design", "Frontend (HTML/CSS/JS)"],
            "short_note": "Looking for a Figma pro who can craft interactive dashboards and pitch decks for our FinTech platform."
        },
        {
            "team_id": team1.id,
            "event_id": events[0].id,
            "role_title": "Pitch & Growth Strategist",
            "required_skills": ["PPT/Pitching", "Product Management"],
            "short_note": "Need someone confident to deliver the 3-minute pitch and answer judge Q&A with clear business metrics."
        },
        {
            "team_id": team2.id,
            "event_id": events[1].id,
            "role_title": "Clinical Research Analyst",
            "required_skills": ["Research & Documentation", "Data Analysis"],
            "short_note": "Validate medical literature datasets and document FDA compliance protocols."
        },
        {
            "team_id": team3.id,
            "event_id": events[2].id,
            "role_title": "Smart Contract Auditor / Security",
            "required_skills": ["Cybersecurity", "Blockchain & Web3"],
            "short_note": "Audit Solidity logic for re-entrancy and verify gas efficiency."
        },
        {
            "team_id": team4.id,
            "event_id": events[3].id,
            "role_title": "DevOps & Cloud Engineer",
            "required_skills": ["Cloud & DevOps (AWS/Docker)", "Python"],
            "short_note": "Set up AWS IoT Core brokers and automated telemetry CI/CD pipelines."
        },
        {
            "team_id": team5.id,
            "event_id": events[4].id,
            "role_title": "Design & UX Lead",
            "required_skills": ["UI/UX Design", "React"],
            "short_note": "Design engaging educational micro-interactions in Tailwind CSS and Figma."
        }
    ]

    for sd in seats_data:
        req_sk = sd.pop("required_skills")
        seat = OpenSeat(**sd, status="open")
        seat.required_skills = req_sk
        db.add(seat)

    db.commit()
    print("[OK] Created 6 open seats.")

    # 6. Seed some friendly sample messages in Team 1
    print("Seeding initial messages and invites...")
    msg1 = TeamMessage(
        team_id=team1.id,
        sender_id=demo_user.id,
        content="Hey Ananya! Welcome to FinVision Alpha. Excited to build this together!"
    )
    msg2 = TeamMessage(
        team_id=team1.id,
        sender_id=u2.id,
        content="Thanks Aarav! I've already outlined the transformer architecture for fraud classification. Now let's find an awesome UI/UX designer and pitch lead!"
    )
    db.add(msg1)
    db.add(msg2)

    # Seed an incoming invite to the demo user
    inv1 = Invite(
        sender_id=u3.id,
        receiver_id=demo_user.id,
        event_id=events[0].id,
        team_id=None,
        message="Hey Aarav! Loved your backend projects on GitHub. Want to team up for ACE Hackathon 5.0?",
        proposed_role="Backend Lead",
        status="pending"
    )
    db.add(inv1)

    # Seed peer feedback for demo user to establish baseline reliability score
    fb1 = Feedback(
        event_id=events[0].id,
        team_id=team1.id,
        from_user_id=u2.id,
        to_user_id=demo_user.id,
        rating=5,
        comment="Incredible work ethic, crystal clear communication, and robust clean API code."
    )
    fb1.tags = ["Reliable", "Great communicator", "Technical wizard"]
    db.add(fb1)

    db.commit()
    db.close()

    print("\n" + "="*70)
    print(">>> TEAMUP SEED COMPLETE!")
    print(f">> Demo Login Account: demo@mait.ac.in")
    print(f">> Demo Password:       demo1234")
    print(f">> Total Users:         {len(users)}")
    print(f">> Total Events:        {len(events)}")
    print(f">> Total Teams:         5")
    print(f">> Total Open Seats:    6")
    print("="*70 + "\n")

if __name__ == "__main__":
    seed_database()
