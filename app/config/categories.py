"""
Categories derived directly from students.csv and teams.csv.
Used across backend validation, matching models, and frontend UI.
"""

# 31 Distinct Skills grouped logically for the UI
SKILLS = [
    "Blockchain", "Business Analysis", "C++", "CSS", "Cloud Computing",
    "Communication", "Computer Vision", "Cybersecurity", "Data Analysis",
    "Data Science", "Deep Learning", "Django", "FastAPI", "Figma",
    "Flask", "Graphic Design", "HTML", "IoT", "Java", "JavaScript",
    "Machine Learning", "Marketing", "MongoDB", "NLP", "Presentation",
    "Project Management", "Python", "React", "Research", "SQL", "UI/UX Design"
]

SKILL_GROUPS = {
    "Programming": ["Python", "C++", "Java", "JavaScript", "HTML", "CSS"],
    "Web/Backend": ["React", "Django", "Flask", "FastAPI", "SQL", "MongoDB"],
    "Data & AI": [
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "Data Science", "Data Analysis", "Business Analysis", "Research"
    ],
    "Cloud & Systems": ["Cloud Computing", "Cybersecurity", "Blockchain", "IoT"],
    "Design": ["UI/UX Design", "Figma", "Graphic Design"],
    "Business & Soft Skills": ["Marketing", "Communication", "Presentation", "Project Management"]
}

# Skill proficiency: Integer 1-5
PROFICIENCY_LEVELS = [1, 2, 3, 4, 5]
PROFICIENCY_LABELS = {
    1: "Basic",
    2: "Novice",
    3: "Intermediate",
    4: "Advanced",
    5: "Expert"
}

# 31 Distinct Interests from the dataset
INTERESTS = [
    "AR/VR", "Analytics", "Artificial Intelligence", "Bioinformatics",
    "Blockchain Technology", "Cloud Architecture", "Computer Vision",
    "Cybersecurity", "Data Science", "Database Systems", "Deep Learning",
    "DevOps", "Digital Marketing", "EdTech", "Edge Computing",
    "Entrepreneurship", "FinTech", "Game Development", "Healthcare Technology",
    "Human-Computer Interaction", "IoT Systems", "Machine Learning",
    "Mobile Development", "Natural Language Processing", "Open Source",
    "Research & Academia", "Robotics", "Social Impact Tech",
    "Sustainability Tech", "UI/UX Research", "Web Development"
]

# Experience Levels
EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]

# Availability Options (Replaces earlier weekdays/weekends/evenings)
AVAILABILITY_OPTIONS = ["Full-time", "Part-time", "Weekends"]

# Preferred Team Sizes
PREFERRED_TEAM_SIZES = [2, 3, 4, 5, 6, 7, 8]

# 21 Distinct Preferred Roles
PREFERRED_ROLES = [
    "Backend Developer", "Blockchain Developer", "Business Analyst",
    "Cloud Engineer", "Computer Vision Engineer", "Cybersecurity Analyst",
    "Data Analyst", "Data Scientist", "DevOps Engineer", "Frontend Developer",
    "Full Stack Developer", "Graphic Designer", "IoT Engineer",
    "Machine Learning Engineer", "Marketing Strategist", "NLP Engineer",
    "Presenter/Communicator", "Project Manager", "Research Lead",
    "Robotics", "UI/UX Designer"
]

# 10 Distinct Collaboration Preference Sentences
COLLABORATION_PREFERENCES = [
    "Comfortable with both in-person and hybrid team settings",
    "Enjoys brainstorming sessions and open creative collaboration",
    "Favors pair programming and frequent code reviews",
    "Likes structured sprint cycles with retrospectives",
    "Prefers a flat team hierarchy with shared ownership",
    "Prefers async communication with weekly syncs",
    "Prefers remote collaboration using shared tools like Notion and Slack",
    "Thrives in agile environments with daily standups",
    "Works best with clearly defined tasks and milestones",
    "Works well with mentorship-style dynamics in a cross-functional team"
]

# 20 Distinct Colleges from data + top colleges including MAIT for demo flow
COLLEGES = [
    "Bayside College", "Brightwater College", "Cedarbrook University",
    "Cliffside Institute", "Eastview College of Engineering", "Elmswood University",
    "Greenfield University", "Harborview University", "Lakewood Polytechnic",
    "Maplewood College of Computing", "Northshore College",
    "Oakridge Institute of Technology", "Pinehurst Polytechnic",
    "Redwood Institute of Science", "Ridgemont Institute",
    "Riverdale College of Technology", "Silverstone University",
    "Stonecrest College", "Sunnyside University", "Westmoor University",
    "Maharaja Agrasen Institute of Technology (MAIT)", "IIT Bombay",
    "BITS Pilani", "Delhi Technological University (DTU)"
]
