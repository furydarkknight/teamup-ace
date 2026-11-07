"""
Seed expansion data for ACE TeamUp platform.
Seeds:
- Demo accounts for all roles (student, organizer, recruiter, mentor, admin)
- 10 Colleges & 15 Clubs
- 15 Companies with 40 Jobs/Internships
- 60 Opportunities across all 16 types (linking existing events)
- 40 Courses across SKILLS list with modules, lessons, and quizzes
- 6 Learning Paths
- 25 Skill Assessments (levels 1-5 with MCQs)
- 30 Mentors with available slots & 40 Alumni
- Demo user seeded data: applications, certificates, verified skills, badges, notifications
"""

import json
import random
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.auth import hash_password
from app.config import (
    SKILLS, INTERESTS, PREFERRED_ROLES, COLLEGES,
    COLLABORATION_PREFERENCES, EXPERIENCE_LEVELS
)
from app.models import (
    User, Event, Team, TeamMember, Feedback
)
from app.models_expansion import (
    Opportunity, Company, JobPosting, Resume, JobAlert,
    Application, SavedItem, Notification, Course, CourseModule,
    CourseLesson, CourseEnrollment, LessonProgress, Assessment,
    AssessmentAttempt, LearningPath, Certificate, VerifiedSkill,
    Badge, UserBadge, MentorProfile, MentorshipSession, AlumniProfile,
    ReferralRequest, ForumThread, ForumPost, College, Club,
    ProjectSubmission, JudgingScore, TrialSprint, BackupBench, TeamTask
)


def seed_expansion():
    db = SessionLocal()
    print(">>> Starting Platform Expansion Seeding...")

    # ----------------------------------------------------
    # 1. DEMO ACCOUNTS FOR ALL ROLES
    # ----------------------------------------------------
    demo_accounts = [
        {
            "email": "demo@mait.ac.in",
            "name": "Aarav Sharma",
            "role": "student",
            "roles": ["student"],
            "college": "Maharaja Agrasen Institute of Technology (MAIT)",
            "headline": "Full Stack Dev & ML Enthusiast | 3x Hackathon Finalist",
            "username": "aaravsharma",
            "points": 340,
            "is_verified": True
        },
        {
            "email": "organizer@delhitechexpo.edu",
            "name": "Dr. Rajesh Verma",
            "role": "organizer",
            "roles": ["organizer"],
            "college": "Delhi Technological University (DTU)",
            "headline": "Convenor - Delhi Tech Expo & Inter-University Hackathons",
            "username": "rajeshverma_dtu",
            "points": 1200,
            "is_verified": True
        },
        {
            "email": "recruiter@nexuslabs.com",
            "name": "Pooja Mehra",
            "role": "recruiter",
            "roles": ["recruiter"],
            "college": "BITS Pilani",
            "company_name": "Nexus Labs",
            "headline": "Head of Early Talent Acquisition @ Nexus Labs",
            "username": "poojamehra_talent",
            "points": 850,
            "is_verified": True
        },
        {
            "email": "mentor@aiimsalumni.ac.in",
            "name": "Vikram Malhotra",
            "role": "mentor",
            "roles": ["mentor", "student"],
            "college": "IIT Bombay",
            "headline": "Senior AI Architect @ CloudScale | Ex-Google | Mentor to 100+ Students",
            "username": "vikram_ai",
            "points": 2100,
            "is_verified": True
        },
        {
            "email": "admin@allcollegeevent.com",
            "name": "ACE Administrator",
            "role": "admin",
            "roles": ["admin"],
            "college": "AllCollegeEvent HQ",
            "headline": "Super Admin - AllCollegeEvent.com Global Platform",
            "username": "ace_admin",
            "points": 5000,
            "is_verified": True
        }
    ]

    for acc in demo_accounts:
        user = db.query(User).filter(User.email == acc["email"]).first()
        if not user:
            user = User(
                email=acc["email"],
                hashed_password=hash_password("demo1234" if acc["role"] != "admin" else "admin1234"),
                name=acc["name"],
                college=acc["college"],
                city="Delhi",
                year="Senior Faculty / Alumni" if acc["role"] in ["organizer", "mentor", "admin"] else "3rd Year",
                role=acc["role"],
                roles_json=json.dumps(acc["roles"]),
                username=acc["username"],
                headline=acc["headline"],
                company_name=acc.get("company_name", ""),
                points=acc["points"],
                is_verified=acc["is_verified"],
                reliability_score=96.0 if acc["role"] in ["student", "mentor"] else 100.0,
                ratings_count=14,
                avatar_url=f"https://api.dicebear.com/7.x/bottts/svg?seed={acc['username']}"
            )
            db.add(user)
            db.flush()
        else:
            user.role = acc["role"]
            user.roles_json = json.dumps(acc["roles"])
            user.username = acc["username"]
            user.headline = acc["headline"]
            if "company_name" in acc:
                user.company_name = acc["company_name"]
            user.points = max(user.points or 0, acc["points"])
            user.is_verified = True
            db.flush()

    db.commit()
    print("[Seed] Demo accounts verified & updated.")

    demo_student = db.query(User).filter(User.email == "demo@mait.ac.in").first()
    organizer_user = db.query(User).filter(User.email == "organizer@delhitechexpo.edu").first()

    # ----------------------------------------------------
    # 2. COLLEGES (10) & CLUBS (15)
    # ----------------------------------------------------
    colleges_data = [
        ("Delhi Technological University (DTU)", "Delhi", "Delhi", ".ac.in", "Premier technical university renowned for engineering research and entrepreneurship."),
        ("Maharaja Agrasen Institute of Technology (MAIT)", "Delhi", "Delhi", ".ac.in", "Top affiliated engineering institution under GGSIPU in North India."),
        ("Indian Institute of Technology Bombay (IIT Bombay)", "Mumbai", "Maharashtra", ".ac.in", "Institute of National Importance known for cutting-edge technology and research."),
        ("BITS Pilani", "Pilani", "Rajasthan", ".ac.in", "Premier private deemed university fostering visionary tech founders and innovators."),
        ("Vellore Institute of Technology (VIT)", "Vellore", "Tamil Nadu", ".ac.in", "Vibrant campus with world-class infrastructure and national hackathon winners."),
        ("RV College of Engineering (RVCE)", "Bangalore", "Karnataka", ".edu.in", "Leading technology institution at the heart of India's Silicon Valley."),
        ("IIIT Hyderabad", "Hyderabad", "Telangana", ".ac.in", "Renowned research university specializing in AI, Computer Vision, and Robotics."),
        ("Netaji Subhas University of Technology (NSUT)", "Delhi", "Delhi", ".ac.in", "Distinguished public engineering university with active coding culture."),
        ("Punjab Engineering College (PEC)", "Chandigarh", "Punjab", ".edu.in", "Centenary technical institute with illustrious alumni across global tech."),
        ("IIT Madras", "Chennai", "Tamil Nadu", ".ac.in", "Consistently ranked #1 engineering university in India by NIRF.")
    ]

    for name, city, state, domain, desc in colleges_data:
        if not db.query(College).filter(College.name == name).first():
            col = College(
                name=name, city=city, state=state, domain=domain,
                description=desc, verified=True, student_count=random.randint(450, 2400)
            )
            db.add(col)
    db.commit()
    print(f"[Seed] 10 Colleges seeded.")

    all_colleges = db.query(College).all()
    clubs_data = [
        ("Google Developer Student Club (GDSC)", "Coding", "Fosters mobile, web, and cloud computing skills with Google technologies."),
        ("ACM Student Chapter", "Coding", "Organizes collegiate coding contests, algorithmic symposiums, and research workshops."),
        ("E-Cell Entrepreneurship Hub", "Business", "Incubates student startups, pitches to VCs, and organizes annual global E-Summits."),
        ("Turing AI & Machine Learning Society", "AI/ML", "Conducts deep-learning research cohorts and Kaggle competition teams."),
        ("Design & UI/UX Guild", "Design", "Fosters product design, user research, wireframing, and Figma prototyping skills."),
        ("Web3 & Blockchain Pioneers", "Web3", "Builds decentralized apps, smart contracts, and attends global ETH hackathons."),
        ("CyberSecurity & Ethical Hacking Cell", "Cybersecurity", "Hosts Capture The Flag (CTF) tournaments and vulnerability disclosure workshops."),
        ("Robotics & Mechatronics Club", "Robotics", "Designs autonomous rovers, drones, and competing in national hardware hackathons."),
        ("Competitive Programming Circle", "Coding", "Focuses on Codeforces, LeetCode, and ICPC algorithmic problem-solving."),
        ("Data Science & Analytics Guild", "AI/ML", "Analyzes real-world datasets, financial models, and predictive algorithms."),
        ("IoT & Embedded Systems Lab", "Hardware", "Builds microcontrollers, Raspberry Pi automation, and smart home hardware."),
        ("Open Source Software Collective", "Coding", "Mentors students for Google Summer of Code (GSoC) and open-source contributions."),
        ("Women in Tech & Leadership", "Community", "Empowers female engineers with mentorship, scholarships, and networking."),
        ("Fintech & Algorithmic Trading Cell", "Fintech", "Explores quantitative finance, automated trading bots, and payment systems."),
        ("Game Dev & AR/VR Studio", "GameDev", "Builds immersive experiences with Unity, Unreal Engine, and WebXR.")
    ]

    for i, (name, cat, desc) in enumerate(clubs_data):
        col = all_colleges[i % len(all_colleges)]
        if not db.query(Club).filter(Club.name == name, Club.college_id == col.id).first():
            club = Club(
                college_id=col.id, name=name, category=cat, description=desc,
                members_count=random.randint(35, 180)
            )
            db.add(club)
    db.commit()
    print(f"[Seed] 15 Clubs seeded.")

    # ----------------------------------------------------
    # 3. COMPANIES (15) & JOBS/INTERNSHIPS (40)
    # ----------------------------------------------------
    companies_data = [
        ("Nexus Labs", "AI & Developer Tools", "50-200 Employees", "Bangalore, India", "Building next-generation agentic AI tools and developer platforms for enterprise teams."),
        ("CloudScale AI", "Cloud Infrastructure", "200-500 Employees", "Hyderabad, India", "High-performance distributed cloud orchestration and GPU-accelerated computing pipelines."),
        ("FinEdge Technologies", "Fintech", "100-250 Employees", "Mumbai, India", "Empowering millions with micro-investment, algorithmic UPI rails, and neo-banking infrastructure."),
        ("HealthPulse Systems", "Healthcare Tech", "50-100 Employees", "Pune, India", "AI-assisted diagnostics, clinical telemetry, and remote patient monitoring software."),
        ("QuantumByte", "Cybersecurity", "20-50 Employees", "Delhi NCR, India", "Zero-trust network architecture, automated penetration testing, and identity security."),
        ("GreenTech Mobility", "CleanTech & EV", "50-150 Employees", "Chennai, India", "Smart EV fleet telematics, battery management algorithms, and charging network software."),
        ("EdVantage Learning", "EdTech", "100-300 Employees", "Bangalore, India", "Personalized adaptive learning algorithms and real-time interactive STEM classrooms."),
        ("SecureNet Cyber", "Enterprise Security", "50-200 Employees", "Noida, India", "Cloud security posture management and automated compliance monitoring."),
        ("DataWeave Analytics", "Big Data & AI", "200-500 Employees", "Bangalore, India", "Competitive digital commerce intelligence, web-scale crawling, and market telemetry."),
        ("MetaCrafters Studio", "Gaming & Web3", "30-80 Employees", "Goa, India", "Creating cross-platform multiplayer games and decentralized digital collectibles."),
        ("BharatPay Solutions", "Payments & Commerce", "500-1000 Employees", "Gurgaon, India", "Empowering 5M+ local merchants with QR soundboxes and credit underwriting."),
        ("BioGenix Informatics", "BioTech & Health", "20-50 Employees", "Hyderabad, India", "Computational genomics, protein folding simulation, and drug discovery workflows."),
        ("AgileDev Systems", "SaaS & Cloud", "100-200 Employees", "Bangalore, India", "Agile workflow automation, kanban collaboration, and continuous deployment tools."),
        ("OmniCommerce Logistics", "Supply Chain", "250-500 Employees", "Mumbai, India", "AI-optimized last-mile logistics dispatch, warehouse automation, and route planning."),
        ("CodeCraft Innovations", "Developer Productivity", "20-50 Employees", "Pune, India", "Automated code review, static analysis, and intelligent linting for large codebases.")
    ]

    for name, ind, size, loc, about in companies_data:
        if not db.query(Company).filter(Company.name == name).first():
            comp = Company(
                name=name, slug=name.lower().replace(" ", "-"), industry=ind,
                size=size, location=loc, about=about,
                culture="Student-friendly engineering culture with high ownership, flexible hours, and rapid growth.",
                verified=True, website=f"https://www.{name.lower().replace(' ', '')}.com"
            )
            db.add(comp)
    db.commit()
    print(f"[Seed] 15 Companies seeded.")

    all_companies = db.query(Company).all()
    job_roles_templates = [
        ("Full Stack Developer Intern", "Software Engineering", "Internship", "Remote", "₹30,000 - ₹45,000/month", ["React", "FastAPI", "Python", "SQL"], "3 Months"),
        ("Machine Learning Research Intern", "AI & Data Science", "Internship", "Hybrid", "₹35,000 - ₹50,000/month", ["Python", "Machine Learning", "Deep Learning", "NLP"], "6 Months"),
        ("Junior Backend Engineer", "Software Engineering", "Full-time", "Bangalore, India", "₹12 - ₹18 LPA", ["Python", "FastAPI", "MongoDB", "Cloud Computing"], "Full-time"),
        ("UI/UX Product Designer", "Design", "Full-time", "Remote", "₹10 - ₹15 LPA", ["UI/UX Design", "Figma", "Research"], "Full-time"),
        ("Frontend Developer Intern", "Software Engineering", "Internship", "Remote", "₹25,000 - ₹35,000/month", ["React", "JavaScript", "HTML", "CSS"], "3 Months"),
        ("Data Analyst Intern", "AI & Data Science", "Internship", "Mumbai, India", "₹25,000 - ₹35,000/month", ["Data Analysis", "SQL", "Python", "Data Science"], "4 Months"),
        ("DevOps & Cloud Engineer Intern", "Infrastructure", "Internship", "Remote", "₹30,000 - ₹40,000/month", ["Cloud Computing", "Cybersecurity", "Python"], "6 Months"),
        ("Cybersecurity Analyst", "Security", "Full-time", "Delhi NCR, India", "₹11 - ₹16 LPA", ["Cybersecurity", "Python", "Research"], "Full-time"),
        ("Associate Product Manager (APM)", "Product", "Full-time", "Bangalore, India", "₹14 - ₹20 LPA", ["Product Management", "Business Analysis", "Communication"], "Full-time"),
        ("Computer Vision Research Fellow", "AI & Data Science", "Part-time", "Remote", "₹40,000/month", ["Computer Vision", "Deep Learning", "Python"], "6 Months")
    ]

    job_counter = 0
    for comp in all_companies:
        # Give each company 2-3 jobs
        count_for_comp = 3 if job_counter < 30 else 2
        for _ in range(count_for_comp):
            if job_counter >= 40:
                break
            template = job_roles_templates[job_counter % len(job_roles_templates)]
            if not db.query(JobPosting).filter(JobPosting.company_id == comp.id, JobPosting.title == template[0]).first():
                job = JobPosting(
                    company_id=comp.id,
                    title=f"{template[0]} ({comp.name})",
                    role_category=template[1],
                    job_type=template[2],
                    work_mode=template[3],
                    location=comp.location if template[3] != "Remote" else "Remote",
                    stipend_salary=template[4],
                    skills_required_json=json.dumps(template[5]),
                    duration=template[6],
                    openings_count=random.randint(1, 4),
                    description=f"Join {comp.name} to build cutting-edge systems. You will collaborate directly with staff engineers and ship features used by thousands of customers daily.",
                    screening_questions_json=json.dumps([
                        "Why are you interested in joining our engineering team?",
                        "Describe a technical project you built using the required skills.",
                        "What is your availability for this role?"
                    ]),
                    deadline=f"Closing in {random.randint(10, 45)} days",
                    is_active=True
                )
                db.add(job)
                job_counter += 1
    db.commit()
    print(f"[Seed] {job_counter} Jobs & Internships seeded.")

    # ----------------------------------------------------
    # 4. OPPORTUNITIES (60) ACROSS ALL 16 TYPES
    # ----------------------------------------------------
    opportunity_types = [
        "Hackathon", "Competition", "Quiz", "Case Study",
        "Coding Challenge", "Workshop", "Webinar", "Conference",
        "Scholarship", "Fellowship", "Internship", "Full-time Job",
        "Part-time Job", "Freelance Project", "Mentorship Program", "Campus Ambassador Role"
    ]

    # First, link existing 8 Events as Opportunities of type Hackathon
    existing_events = db.query(Event).all()
    opp_count = 0
    for ev in existing_events:
        existing_opp = db.query(Opportunity).filter(Opportunity.event_id == ev.id).first()
        if not existing_opp:
            opp = Opportunity(
                event_id=ev.id,
                title=ev.name,
                slug=ev.name.lower().replace(" ", "-")[:80],
                organizer_name="AllCollegeEvent (ACE)",
                organizer_id=organizer_user.id if organizer_user else None,
                type="Hackathon",
                description=ev.description,
                eligibility=f"Teams of {ev.team_size_min}-{ev.team_size_max} students from any recognized college.",
                skills_json=json.dumps(ev.required_roles),
                location_mode=ev.mode,
                location_venue=ev.city_venue,
                start_date=ev.dates,
                deadline=f"Registration ends before {ev.dates}",
                team_size_min=ev.team_size_min,
                team_size_max=ev.team_size_max,
                prize_pool=ev.prize_pool,
                banner_url=ev.banner_url,
                tags_json=json.dumps([ev.theme, ev.mode, "Hackathon"]),
                status="Active",
                is_featured=True
            )
            db.add(opp)
            opp_count += 1
    db.commit()

    # Generate additional opportunities to reach 60 across all 16 types
    titles_by_type = {
        "Hackathon": ["CodeGenesis National Hackathon", "FinTech Sprint 2026", "HealthAI Global Buildathon", "Sustainable Cities HackFest"],
        "Competition": ["National Algorithmic Olympiad", "DataSprint AI Championship", "RoboSumo Nationals", "Smart Mobility Challenge"],
        "Quiz": ["TechTrivia India Cup", "CyberQuest National Security Quiz", "FinKnowledge League", "Python Masters Quiz"],
        "Case Study": ["Tata Business Case Challenge", "Consulting Titans 2026", "Unicorn Growth Strategy Case", "Product teardown Olympiad"],
        "Coding Challenge": ["ByteCode 24-Hour Code Clash", "BugHunt Kernel Challenge", "Frontend Speedrun Contest", "SQL Query Showdown"],
        "Workshop": ["FastAPI & Microservices Bootcamp", "Generative AI & LLM Fine-Tuning", "Figma to Code Masterclass", "Cloud Native DevOps Sprint"],
        "Webinar": ["Inside Google Brain: Future of Agents", "Cracking the APM Interview", "Open Source for Beginners (GSoC)", "Navigating Seed Stage Startups"],
        "Conference": ["National Student Tech Summit 2026", "International Conference on AI & Robotics", "Youth Innovators Conclave", "DevFest Inter-College 2026"],
        "Scholarship": ["Women in Tech Future Leaders Grant", "Rural Innovators Merit Scholarship", "DeepTech Undergraduate Fellowship", "STEM Excellence Award"],
        "Fellowship": ["ACE Product & Engineering Fellowship", "Civic Tech India Fellows", "AI Ethics & Safety Research Fellowship", "NextGen Founders Residency"],
        "Internship": ["Summer Software Engineering Fellowship", "Applied Machine Learning Cohort", "Product Design Apprenticeship", "Quantitative Finance Intern"],
        "Full-time Job": ["Graduate Software Engineer 2026", "Junior Data Scientist Associate", "Associate Cloud Architect", "Developer Relations Engineer"],
        "Part-time Job": ["Technical Content Creator (Python)", "Student Community Evangelist", "Campus Coding Coach", "Open Source Maintenance Lead"],
        "Freelance Project": ["Build MVP for EdTech Startup", "Design Mobile App Wireframes (Figma)", "Scrape & Structure Real Estate Data", "Smart Contract Audit"],
        "Mentorship Program": ["1-on-1 Silicon Valley Mentor Network", "Alumni Career Guidance Cohort", "Hackathon Podium Mentorship", "PhD Research Mentoring Scheme"],
        "Campus Ambassador Role": ["ACE Campus Leader Program 2026", "GitHub Campus Expert Ambassador", "TechCorp College Brand Advocate", "Developer Club Ambassador"]
    }

    target_total = 60
    type_idx = 0
    while opp_count < target_total:
        t = opportunity_types[type_idx % len(opportunity_types)]
        candidates = titles_by_type.get(t, [f"ACE {t} 2026"])
        chosen_title = candidates[random.randint(0, len(candidates) - 1)]
        # Add random suffix if title already used
        if db.query(Opportunity).filter(Opportunity.title == chosen_title).first():
            chosen_title = f"{chosen_title} - Edition {random.randint(2, 9)}"

        mode = random.choice(["Online", "Offline", "Hybrid"])
        skills_sample = random.sample(SKILLS, k=random.randint(2, 5))
        prize = f"₹{random.choice([25, 50, 75, 100, 200, 500])},000" if t in ["Hackathon", "Competition", "Quiz", "Case Study"] else (
            f"₹{random.randint(20, 50)},000/mo" if "Job" in t or "Internship" in t or "Fellowship" in t else "Perks & Swag"
        )

        opp = Opportunity(
            title=chosen_title,
            slug=chosen_title.lower().replace(" ", "-")[:80],
            organizer_name=random.choice([c.name for c in all_colleges] + [comp.name for comp in all_companies]),
            organizer_id=organizer_user.id if organizer_user else None,
            type=t,
            description=f"Participate in {chosen_title} to test your skills, win prestigious awards, and get discovered by top tech employers.",
            eligibility="Open to college students from all recognized universities across India.",
            skills_json=json.dumps(skills_sample),
            location_mode=mode,
            location_venue="Virtual Platform" if mode == "Online" else "New Delhi Convention Centre",
            start_date=f"Starts in {random.randint(5, 30)} days",
            deadline=f"Closing in {random.randint(3, 20)} days",
            team_size_min=1 if t not in ["Hackathon", "Case Study"] else 2,
            team_size_max=1 if t in ["Quiz", "Coding Challenge", "Scholarship", "Campus Ambassador Role"] else 4,
            prize_pool=prize,
            banner_url=f"https://images.unsplash.com/photo-{random.choice(['1517245386807-bb43f82c33c4', '1504384308090-c894fdcc538d', '1522071820081-009f0129c71c', '1531482615713-2afd69097998'])}?auto=format&fit=crop&w=1200&q=80",
            tags_json=json.dumps([t, mode, skills_sample[0]]),
            status="Closing Soon" if random.random() < 0.25 else "Active",
            is_featured=random.random() < 0.2
        )
        db.add(opp)
        opp_count += 1
        type_idx += 1

    db.commit()
    print(f"[Seed] 60 Opportunities seeded across all 16 types.")

    # ----------------------------------------------------
    # 5. COURSES (40) ACROSS SKILLS LIST & LESSONS
    # ----------------------------------------------------
    course_templates = [
        ("Python for Production & Microservices", "Python", "Beginner", "Learn idiomatic Python, concurrency with asyncio, typing, and production-grade architectures."),
        ("FastAPI Masterclass: Modern REST APIs", "FastAPI", "Intermediate", "Build scalable asynchronous APIs, Pydantic data schemas, dependency injection, and JWT auth."),
        ("Full Stack React & Modern Frontend", "React", "Beginner", "Master React 18 hooks, state management, Tailwind styling, and responsive UI components."),
        ("Machine Learning from Scratch with Scikit-Learn", "Machine Learning", "Intermediate", "Implement classification, regression, clustering, ensemble models, and feature engineering."),
        ("Deep Learning & PyTorch Fundamentals", "Deep Learning", "Advanced", "Train deep neural networks, CNNs, Transformers, and customize PyTorch loss functions."),
        ("Natural Language Processing with Transformers", "NLP", "Advanced", "Fine-tune BERT, Hugging Face models, RAG architectures, and sentence embeddings."),
        ("Computer Vision: OpenCV to YOLOv8", "Computer Vision", "Intermediate", "Object detection, image segmentation, facial landmarking, and real-time video streams."),
        ("Data Analysis & Visualization with Pandas", "Data Analysis", "Beginner", "Wrangle noisy datasets, perform statistical aggregations, and design dashboards with Seaborn."),
        ("Data Science & Feature Engineering Pipeline", "Data Science", "Intermediate", "End-to-end data pipelines, exploratory data analysis (EDA), and predictive modeling."),
        ("PostgreSQL & Modern SQL Mastery", "SQL", "Beginner", "Complex queries, window functions, indexing strategies, and database optimization."),
        ("MongoDB & NoSQL Schema Architecture", "MongoDB", "Intermediate", "Document models, aggregation framework, indexing, and high-throughput datastores."),
        ("Cloud Computing with AWS & Serverless", "Cloud Computing", "Intermediate", "Deploy scalable applications on EC2, S3, Lambda, and configure VPC networks."),
        ("Cybersecurity & Ethical Hacking Essentials", "Cybersecurity", "Beginner", "Vulnerability assessment, network reconnaissance, OWASP Top 10, and defense techniques."),
        ("Blockchain & Ethereum Smart Contracts", "Blockchain", "Advanced", "Write Solidity contracts, deploy on testnets, and build secure Web3 decentralized apps."),
        ("Internet of Things (IoT) & Embedded C++", "IoT", "Intermediate", "Sensor telemetry, MQTT message brokers, Raspberry Pi, and hardware automation."),
        ("Modern C++ for High-Performance Systems", "C++", "Intermediate", "Memory safety, pointers, templates, STL containers, and algorithmic optimization."),
        ("Java Enterprise Development with Spring Boot", "Java", "Intermediate", "Dependency injection, JPA Hibernate ORM, microservice architecture, and security."),
        ("Modern JavaScript & ES6+ Architecture", "JavaScript", "Beginner", "Async/await, closures, promises, DOM manipulation, and modular design patterns."),
        ("HTML5 & Responsive CSS Layouts", "HTML", "Beginner", "Semantic markup, CSS Grid, Flexbox, accessible design, and mobile-first principles."),
        ("Tailwind CSS: Rapid Modern Web Design", "CSS", "Beginner", "Utility-first workflows, custom design systems, dark mode, and animations."),
        ("Django Web Framework for Rapid MVPs", "Django", "Intermediate", "Django ORM, template engine, authentication, and REST framework integrations."),
        ("Flask Microframework: Lightweight Web Apps", "Flask", "Beginner", "Routing, Blueprints, Jinja templating, and lightweight RESTful endpoints."),
        ("Business Analysis & Strategic Decision Making", "Business Analysis", "Beginner", "Business requirement documents (BRD), KPI modeling, and stakeholder alignment."),
        ("Academic & Tech Research Methodology", "Research", "Intermediate", "Literature reviews, experimental benchmarking, LaTeX formatting, and publishing papers."),
        ("UI/UX Design Systems & User Research", "UI/UX Design", "Beginner", "User personas, wireframing, heuristic evaluation, and interactive design tokens."),
        ("Figma from Wireframe to High-Fidelity Prototype", "Figma", "Beginner", "Auto-layout, components, interactive prototyping, and design system handover."),
        ("Graphic Design & Visual Branding for Startups", "Graphic Design", "Beginner", "Color theory, typography hierarchy, social branding, and visual marketing assets."),
        ("Growth Marketing & Acquisition for Tech Startups", "Marketing", "Beginner", "Customer acquisition channels, SEO, viral loops, and conversion rate optimization."),
        ("Effective Communication for Software Engineers", "Communication", "Beginner", "Clear pull request descriptions, documentation, sprint syncs, and team alignment."),
        ("Pitching to Investors & Hackathon Judges", "Presentation", "Beginner", "Structuring 3-minute hackathon pitches, storytelling, slides, and Q&A handling."),
        ("Agile & Scrum Project Management for Developers", "Project Management", "Beginner", "Sprint planning, backlog grooming, velocity tracking, and Jira/Notion workflows."),
        ("Full Stack FastAPI + React Integration", "FastAPI", "Intermediate", "CORS, JWT authentication flows, file uploads, and state synchronization."),
        ("Docker & Containerization for Developers", "Cloud Computing", "Beginner", "Dockerfiles, multi-stage builds, docker-compose, and container networking."),
        ("DevOps CI/CD Pipelines with GitHub Actions", "Cloud Computing", "Intermediate", "Automated testing, linting, semantic versioning, and cloud deployments."),
        ("Applied Machine Learning for Hackathon MVPs", "Machine Learning", "Beginner", "Pickle models, inference APIs, prompt engineering, and lightweight ML prototypes."),
        ("Big Data Processing with Apache Spark", "Data Science", "Advanced", "RDDs, DataFrames, distributed aggregations, and large-scale data lakes."),
        ("Prompt Engineering & LLM Application Development", "NLP", "Intermediate", "Few-shot prompting, LangChain agents, vector databases, and OpenAI/Gemini APIs."),
        ("Mobile App Development with Flutter & Dart", "React", "Beginner", "Cross-platform iOS and Android apps with beautiful native UI."),
        ("API Security & Rate Limiting Architectures", "Cybersecurity", "Intermediate", "Token bucket algorithms, DDoS defense, OAuth2, and SSL/TLS pinning."),
        ("Competitive Algorithm Design & Dynamic Programming", "C++", "Advanced", "Greedy algorithms, graph theory, memoization, and complex DP states.")
    ]

    for title, skill, lvl, desc in course_templates:
        if not db.query(Course).filter(Course.title == title).first():
            course = Course(
                title=title,
                slug=title.lower().replace(" ", "-")[:80],
                description=desc,
                skill_tags_json=json.dumps([skill, lvl]),
                level=lvl,
                duration=f"{random.randint(4, 12)} Hours",
                is_free=True,
                mock_price=0,
                instructor_name="ACE Engineering Faculty",
                instructor_title="Senior Industry Practitioner",
                rating=round(random.uniform(4.7, 4.98), 2),
                enrolled_count=random.randint(120, 1850)
            )
            db.add(course)
            db.flush()

            # Add 3 modules per course
            module_names = ["1. Foundations & Setup", "2. Core Architectures & Implementation", "3. Capstone Project & Deployment"]
            for m_idx, m_name in enumerate(module_names):
                mod = CourseModule(course_id=course.id, title=m_name, order_num=m_idx + 1)
                db.add(mod)
                db.flush()

                # Add 2 lessons per module
                lessons_meta = [
                    (f"Concepts & Architectural Patterns", "text", f"Detailed breakdown of {title}. Understanding the underlying core mechanics and industry best practices."),
                    (f"Hands-on Lab & Mini-Challenge", "quiz", f"Practical implementation exercise and knowledge-check quiz.")
                ]
                for l_idx, (l_title, l_type, l_content) in enumerate(lessons_meta):
                    lesson = CourseLesson(
                        module_id=mod.id,
                        title=l_title,
                        order_num=l_idx + 1,
                        content_type=l_type,
                        content=l_content,
                        quiz_data_json=json.dumps([
                            {
                                "question": f"What is a primary architectural benefit of using {skill} in modern software?",
                                "options": ["High scalability and maintainability", "Slow compile times", "Lack of community support", "No typed interfaces"],
                                "answer_index": 0
                            }
                        ]) if l_type == "quiz" else "[]"
                    )
                    db.add(lesson)

    db.commit()
    print(f"[Seed] 40 Courses with modules and lessons seeded.")

    # ----------------------------------------------------
    # 6. LEARNING PATHS (6)
    # ----------------------------------------------------
    all_courses = db.query(Course).all()
    c_ids = [c.id for c in all_courses]
    learning_paths_data = [
        ("Full Stack Developer Track", "Full Stack Developer", "Comprehensive pathway to master frontend, backend, databases, and deployment.", c_ids[:4], "Build an AI-powered notes application with collaborative editing.", "fa-laptop-code"),
        ("Machine Learning Engineer Track", "Machine Learning Engineer", "From statistical fundamentals to fine-tuning transformers and deploying real-time inference APIs.", c_ids[3:7], "Deploy a real-time semantic document search engine.", "fa-brain"),
        ("Data Science & Analytics Specialist", "Data Scientist", "Master data wrangling, exploratory data analysis, visual storytelling, and predictive algorithms.", c_ids[7:11], "End-to-end customer churn prediction pipeline with dashboard.", "fa-chart-pie"),
        ("Cloud & DevOps Architecture Track", "Cloud Engineer", "Master containerization, infrastructure-as-code, CI/CD pipelines, and cloud security.", c_ids[11:15], "Multi-region Kubernetes deployment with automated GitHub Actions.", "fa-cloud"),
        ("UI/UX Product Design Master", "UI/UX Designer", "Design systems, Figma mastery, user journey mapping, and usability testing.", c_ids[24:28], "Complete redesign of a fintech micro-investment mobile application.", "fa-pen-ruler"),
        ("Cybersecurity Defense & Analyst", "Cybersecurity Analyst", "Hands-on threat analysis, network defense, ethical hacking, and vulnerability remediation.", c_ids[12:16], "Security audit report and automated vulnerability scanner.", "fa-shield-halved")
    ]

    for title, role, desc, courses_sub, capstone, icon in learning_paths_data:
        if not db.query(LearningPath).filter(LearningPath.title == title).first():
            lp = LearningPath(
                title=title,
                role_target=role,
                description=desc,
                course_ids_json=json.dumps(courses_sub),
                capstone_project_json=json.dumps({"title": f"{title} Capstone", "description": capstone}),
                badge_icon=icon
            )
            db.add(lp)
    db.commit()
    print(f"[Seed] 6 Learning Paths seeded.")

    # ----------------------------------------------------
    # 7. SKILL ASSESSMENTS (25)
    # ----------------------------------------------------
    skills_for_assessments = SKILLS[:25]
    for skill in skills_for_assessments:
        if not db.query(Assessment).filter(Assessment.skill_name == skill).first():
            questions = [
                {
                    "question": f"Which of the following best describes the core strength of {skill}?",
                    "options": [
                        f"Standardized performance, rich ecosystem, and robust tooling for {skill}",
                        "Deprecated syntax that should not be used in modern systems",
                        "High latency and single-threaded blocking only",
                        "Incompatibility with modern web protocols"
                    ],
                    "correct_idx": 0,
                    "explanation": f"{skill} is widely adopted across industry for its reliability, developer velocity, and strong ecosystem."
                },
                {
                    "question": f"What is considered an anti-pattern when designing architecture with {skill}?",
                    "options": [
                        "Hardcoding credentials and unhandled global exceptions",
                        "Writing modular unit tests",
                        "Using typed interfaces and linter validation",
                        "Adopting standard naming conventions"
                    ],
                    "correct_idx": 0,
                    "explanation": "Hardcoding credentials and ignoring error handling leads to critical security and operational failures."
                },
                {
                    "question": f"When scaling systems built with {skill}, what is the recommended practice?",
                    "options": [
                        "Stateless horizontal scaling with caching layers",
                        "Storing session state in memory on single nodes",
                        "Disabling all logging to reduce disk write overhead",
                        "Running without any database indexing"
                    ],
                    "correct_idx": 0,
                    "explanation": "Stateless horizontal scaling allows independent replicas to handle traffic spikes smoothly."
                }
            ]

            ass = Assessment(
                skill_name=skill,
                title=f"{skill} Proficiency Benchmark",
                description=f"Validate your real-world proficiency in {skill}. Scoring 70%+ awards a verified level 3+ skill badge.",
                level=random.choice([3, 4]),
                questions_json=json.dumps(questions),
                duration_minutes=15,
                passing_score=70
            )
            db.add(ass)
    db.commit()
    print(f"[Seed] 25 Skill Assessments seeded.")

    # ----------------------------------------------------
    # 8. MENTORS (30) & ALUMNI (40)
    # ----------------------------------------------------
    students_sample = db.query(User).filter(User.role == "student").limit(80).all()
    mentor_counter = 0
    alumni_counter = 0

    companies_names = [c.name for c in all_companies]
    for idx, u in enumerate(students_sample):
        if idx < 30 and not db.query(MentorProfile).filter(MentorProfile.user_id == u.id).first():
            # Create mentor profile
            mp = MentorProfile(
                user_id=u.id,
                company=random.choice(companies_names),
                job_title=random.choice(["Staff Engineer", "Senior ML Researcher", "VP of Product", "Lead Architect", "Principal Designer"]),
                expertise_skills_json=json.dumps(random.sample(SKILLS, k=3)),
                years_experience=random.randint(3, 10),
                bio=f"Passionate about mentoring the next generation of engineers and hackathon winners. Specializes in scalable architectures and career growth.",
                rating=round(random.uniform(4.8, 5.0), 2),
                sessions_count=random.randint(8, 45)
            )
            db.add(mp)
            u.is_mentor = True
            mentor_counter += 1

        elif idx >= 30 and idx < 70 and not db.query(AlumniProfile).filter(AlumniProfile.user_id == u.id).first():
            ap = AlumniProfile(
                user_id=u.id,
                college=u.college,
                graduation_year=str(random.choice([2021, 2022, 2023, 2024])),
                company=random.choice(companies_names),
                current_role=random.choice(["Software Engineer II", "Senior Data Analyst", "Cloud Architect", "Product Designer"]),
                can_refer=True,
                linkedin_url=f"https://linkedin.com/in/{u.name.lower().replace(' ', '')}"
            )
            db.add(ap)
            alumni_counter += 1

    db.commit()
    print(f"[Seed] {mentor_counter} Mentors & {alumni_counter} Alumni seeded.")

    # ----------------------------------------------------
    # 9. BADGES & SEEDED DATA FOR DEMO STUDENT (Aarav Sharma)
    # ----------------------------------------------------
    badge_defs = [
        ("FIRST_HACKATHON", "Hackathon Pioneer", "Formed or joined your first official hackathon team on TeamUp.", "fa-trophy", "hackathon"),
        ("VERIFIED_STUDENT", "Verified Campus Scholar", "Verified identity with an official college email address (.edu/.ac.in).", "fa-user-check", "community"),
        ("HIGH_RELIABILITY", "Reliability Champion", "Maintained an exceptional 95+ peer reliability rating across events.", "fa-star", "community"),
        ("SKILL_ASSESSED", "Certified Practitioner", "Successfully passed an official skill benchmark assessment.", "fa-certificate", "learning"),
        ("TEAM_BUILDER", "Master Collaborator", "Successfully formed a team with zero complementary skill gaps.", "fa-users", "teams")
    ]

    for code, bname, bdesc, bicon, bcat in badge_defs:
        if not db.query(Badge).filter(Badge.code == code).first():
            b = Badge(code=code, name=bname, description=bdesc, icon=bicon, category=bcat)
            db.add(b)
    db.commit()

    all_badges = db.query(Badge).all()
    if demo_student:
        # Give demo user badges
        for b in all_badges[:4]:
            if not db.query(UserBadge).filter(UserBadge.user_id == demo_student.id, UserBadge.badge_id == b.id).first():
                db.add(UserBadge(user_id=demo_student.id, badge_id=b.id))

        # Give demo user a primary Resume
        if not db.query(Resume).filter(Resume.user_id == demo_student.id).first():
            res = Resume(
                user_id=demo_student.id,
                title="Aarav Sharma - Software & ML Resume",
                template_name="modern",
                data_json=json.dumps({
                    "summary": "Passionate 3rd-year computer engineering student with proven track record building full-stack web platforms and ML matching systems. 3x hackathon finalist with strong grasp of FastAPI, React, and Python.",
                    "education": [
                        {"degree": "B.Tech in Computer Science & Engineering", "institution": "Maharaja Agrasen Institute of Technology (MAIT)", "year": "2023 - 2027", "score": "9.2 CGPA"}
                    ],
                    "experience": [
                        {"role": "Full Stack Engineering Intern", "company": "Nexus Labs", "duration": "Summer 2025", "details": "Built real-time telemetry dashboards and reduced API latency by 35% using FastAPI caching."}
                    ],
                    "projects": [
                        {"name": "TeamUp by ACE", "tech": "FastAPI, Tailwind, SQLite, Sentence-Transformers", "description": "Modular hackathon team formation engine using skill-complement matching and explainable AI."},
                        {"name": "NeuroScan Health", "tech": "PyTorch, React, Python", "description": "Microservice diagnosing pulmonary anomalies from chest X-rays with 94% accuracy."}
                    ],
                    "skills": ["Python", "FastAPI", "React", "Machine Learning", "SQL", "Cloud Computing"],
                    "certifications": ["ACE Certified FastAPI Microservices Architect", "Scikit-Learn Machine Learning Specialist"]
                }),
                is_default=True
            )
            db.add(res)

        # Give demo user sample Certificates
        sample_certs = [
            ("ACE-CERT-2026-F891", "FastAPI & Microservices Architecture", "course", "AllCollegeEvent (ACE) Academy"),
            ("ACE-CERT-2026-H502", "1st Place Winner - ACE International Hackathon 5.0", "hackathon_win", "AllCollegeEvent & FinTech Alliance"),
            ("ACE-CERT-2026-P314", "Python Benchmark Assessment - Level 4 Expert", "assessment", "ACE Engineering Skills Board")
        ]
        for uid, ctitle, ctype, cissuer in sample_certs:
            if not db.query(Certificate).filter(Certificate.unique_id == uid).first():
                cert = Certificate(
                    unique_id=uid,
                    user_id=demo_student.id,
                    recipient_name=demo_student.name,
                    title=ctitle,
                    issuer=cissuer,
                    certificate_type=ctype,
                    qr_code_data=f"https://allcollegeevent.com/verify/{uid}",
                    metadata_json=json.dumps({"grade": "Distinction", "score": "98%", "verified": True})
                )
                db.add(cert)

        # Give demo user Verified Skills
        for skill_name in ["Python", "FastAPI", "Machine Learning"]:
            if not db.query(VerifiedSkill).filter(VerifiedSkill.user_id == demo_student.id, VerifiedSkill.skill_name == skill_name).first():
                db.add(VerifiedSkill(
                    user_id=demo_student.id,
                    skill_name=skill_name,
                    verification_type="assessment",
                    proof_link=f"https://allcollegeevent.com/verify/ACE-CERT-2026-P314"
                ))

        # Give demo user Sample Applications
        first_opp = db.query(Opportunity).first()
        first_job = db.query(JobPosting).first()
        if first_opp and not db.query(Application).filter(Application.user_id == demo_student.id, Application.opportunity_id == first_opp.id).first():
            db.add(Application(
                user_id=demo_student.id,
                opportunity_id=first_opp.id,
                application_type="opportunity",
                status="Registered",
                status_timeline_json=json.dumps([
                    {"status": "Applied", "timestamp": "2 days ago", "note": "Team registration submitted."},
                    {"status": "Registered", "timestamp": "Yesterday", "note": "Confirmed team slot."}
                ]),
                cover_note="Excited to build our FinTech solution with a full-stack complement team."
            ))

        if first_job and not db.query(Application).filter(Application.user_id == demo_student.id, Application.job_posting_id == first_job.id).first():
            db.add(Application(
                user_id=demo_student.id,
                job_posting_id=first_job.id,
                application_type="job",
                status="Shortlisted",
                status_timeline_json=json.dumps([
                    {"status": "Applied", "timestamp": "5 days ago", "note": "Application received."},
                    {"status": "Under Review", "timestamp": "3 days ago", "note": "Profile reviewed by hiring team."},
                    {"status": "Shortlisted", "timestamp": "Today", "note": "Invited for Round 1 Technical Interview."}
                ]),
                expected_stipend="₹35,000/month",
                cover_note="I have hands-on experience building FastAPI microservices and would love to contribute to your core backend."
            ))

        # Give demo user Notifications
        sample_notifs = [
            ("🎉 You've been Shortlisted!", f"Nexus Labs shortlisted your application for Full Stack Developer Intern.", "#myspace", "application"),
            ("⚡ New 94% Skill Match!", f"Ananya Iyer covers UI/UX and PPT Pitching which complement your team for ACE Hackathon 5.0.", "#events", "match"),
            ("⏳ Deadline Alert: T-2 Days", f"Registration for ACE International Hackathon 5.0 closes in 48 hours.", "#events", "deadline"),
            ("🤝 Teammate Joined", f"Ishaan Patel accepted your invitation to join FinVision Alpha.", "#team-1", "invite")
        ]
        for ntitle, nmsg, nlink, ntype in sample_notifs:
            if not db.query(Notification).filter(Notification.user_id == demo_student.id, Notification.title == ntitle).first():
                db.add(Notification(
                    user_id=demo_student.id,
                    title=ntitle,
                    message=nmsg,
                    link=nlink,
                    notification_type=ntype,
                    is_read=False
                ))

    db.commit()
    print("[Seed] Demo student portfolio, resume, certificates, and applications seeded.")

    # ----------------------------------------------------
    # 10. ADVANCED TEAM FEATURES SEED (Team 1)
    # ----------------------------------------------------
    team1 = db.query(Team).first()
    if team1 and demo_student:
        # Add tasks to team 1 kanban
        sample_tasks = [
            ("Finalize System Architecture & Data Schema", "in_progress", "high"),
            ("Build Figma Wireframes for Teammate Finder", "done", "medium"),
            ("Train Sentence-Transformers Matching Model", "todo", "high"),
            ("Prepare 3-Minute Slide Deck for Judging", "todo", "medium")
        ]
        for ttitle, tstat, tprio in sample_tasks:
            if not db.query(TeamTask).filter(TeamTask.team_id == team1.id, TeamTask.title == ttitle).first():
                db.add(TeamTask(
                    team_id=team1.id,
                    title=ttitle,
                    assigned_to_user_id=demo_student.id,
                    status=tstat,
                    priority=tprio
                ))

        # Add a trial sprint
        if not db.query(TrialSprint).filter(TrialSprint.team_id == team1.id).first():
            db.add(TrialSprint(
                team_id=team1.id,
                user_id=demo_student.id,
                prompt="Implement a mock endpoint that calculates cosine similarity between two user skill vectors within 24 hours.",
                status="Active"
            ))

    db.commit()
    db.close()
    print("\n" + "="*70)
    print(">>> PLATFORM EXPANSION SEEDING COMPLETE!")
    print(">> 60 Opportunities across 16 types")
    print(">> 15 Companies & 40 Jobs/Internships")
    print(">> 40 Courses & 6 Learning Paths")
    print(">> 25 Skill Assessments")
    print(">> 30 Mentors & 40 Alumni")
    print(">> Demo Accounts Ready: Student, Organizer, Recruiter, Mentor, Admin")
    print("="*70 + "\n")


if __name__ == "__main__":
    seed_expansion()
