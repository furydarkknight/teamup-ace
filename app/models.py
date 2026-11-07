from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=True) # e.g. "S0001"
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    name = Column(String(100), nullable=False)
    college = Column(String(150), nullable=False, index=True)
    city = Column(String(100), default="Delhi")
    year = Column(String(50), default="3rd Year")
    short_bio = Column(Text, default="")
    bio = Column(Text, default="")
    avatar_url = Column(String(255), default="")

    # JSON stored fields
    skills_json = Column(Text, default="[]")                 # List of skill names: ["Python", "C++"]
    skill_proficiency_json = Column(Text, default="{}")      # Dict skill -> 1-5 integer: {"Python": 4}
    interests_json = Column(Text, default="[]")              # List of strings: ["AI & ML"]
    project_experience_json = Column(Text, default="[]")     # List of strings
    preferred_roles_json = Column(Text, default="[]")        # List of strings: ["Full Stack Developer"]
    blocked_users_json = Column(Text, default="[]")          # List of user IDs

    experience_level = Column(String(50), default="Intermediate", index=True) # Beginner, Intermediate, Advanced
    past_hackathons_count = Column(Integer, default=0)
    github_url = Column(String(255), default="")
    linkedin_url = Column(String(255), default="")
    
    # Matching attributes
    availability = Column(String(50), default="Full-time", index=True) # Full-time, Part-time, Weekends
    preferred_team_size = Column(Integer, default=4)                  # 2-8
    collaboration_preference = Column(String(255), default="")        # One of the 10 sentences
    goal = Column(String(50), default="Win Grand Prize")              # Win Grand Prize, Learn & Build Skills, Network

    # Legacy work styles for fallback
    work_schedule = Column(String(50), default="Flexible")
    work_role = Column(String(50), default="Executor / Builder")
    work_vibe = Column(String(50), default="Balanced")

    # Mentor mode
    is_mentor = Column(Boolean, default=False)
    seeking_mentor = Column(Boolean, default=False)

    # Reliability
    reliability_score = Column(Float, default=0.0) # 0-100 score
    ratings_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teams_created = relationship("Team", back_populates="leader", foreign_keys="Team.leader_id")
    memberships = relationship("TeamMember", back_populates="user")
    sent_invites = relationship("Invite", back_populates="sender", foreign_keys="Invite.sender_id")
    received_invites = relationship("Invite", back_populates="receiver", foreign_keys="Invite.receiver_id")
    sent_messages = relationship("TeamMessage", back_populates="sender")
    join_requests = relationship("TeamJoinRequest", back_populates="user")

    @property
    def skills(self):
        try:
            val = json.loads(self.skills_json) if self.skills_json else []
            if isinstance(val, list):
                # Normalizing: if items are dicts with "name", extract name
                return [s["name"] if isinstance(s, dict) and "name" in s else str(s) for s in val]
            return []
        except Exception:
            return []

    @skills.setter
    def skills(self, val):
        if isinstance(val, list):
            names = [s["name"] if isinstance(s, dict) and "name" in s else str(s) for s in val]
            self.skills_json = json.dumps(names)
        else:
            self.skills_json = json.dumps([])

    @property
    def skill_proficiency(self):
        try:
            return json.loads(self.skill_proficiency_json) if self.skill_proficiency_json else {}
        except Exception:
            return {}

    @skill_proficiency.setter
    def skill_proficiency(self, val):
        self.skill_proficiency_json = json.dumps(val if isinstance(val, dict) else {})

    @property
    def skills_items(self):
        """Returns list of {'name': skill, 'level': 1-5} for UI chips and sliders"""
        prof = self.skill_proficiency
        return [{"name": s, "level": prof.get(s, 3)} for s in self.skills]

    @property
    def interests(self):
        try:
            return json.loads(self.interests_json) if self.interests_json else []
        except Exception:
            return []

    @interests.setter
    def interests(self, val):
        self.interests_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def project_experience(self):
        try:
            return json.loads(self.project_experience_json) if self.project_experience_json else []
        except Exception:
            return []

    @project_experience.setter
    def project_experience(self, val):
        self.project_experience_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def preferred_roles(self):
        try:
            return json.loads(self.preferred_roles_json) if self.preferred_roles_json else []
        except Exception:
            return []

    @preferred_roles.setter
    def preferred_roles(self, val):
        self.preferred_roles_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def blocked_users(self):
        try:
            return json.loads(self.blocked_users_json) if self.blocked_users_json else []
        except Exception:
            return []

    @blocked_users.setter
    def blocked_users(self, val):
        self.blocked_users_json = json.dumps(val if isinstance(val, list) else [])


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    tagline = Column(String(300), default="")
    theme = Column(String(100), nullable=False)
    dates = Column(String(100), nullable=False)
    mode = Column(String(50), default="Online") # Online, In-Person, Hybrid
    city_venue = Column(String(150), default="Virtual")
    team_size_min = Column(Integer, default=2)
    team_size_max = Column(Integer, default=4)
    prize_pool = Column(String(100), default="₹1,00,000")
    description = Column(Text, default="")
    required_roles_json = Column(Text, default="[]")
    banner_url = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    teams = relationship("Team", back_populates="event")
    open_seats = relationship("OpenSeat", back_populates="event")

    @property
    def required_roles(self):
        try:
            return json.loads(self.required_roles_json) if self.required_roles_json else []
        except Exception:
            return []

    @required_roles.setter
    def required_roles(self, val):
        self.required_roles_json = json.dumps(val if isinstance(val, list) else [])


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(String(50), unique=True, index=True, nullable=True) # e.g. "T001"
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    name = Column(String(150), nullable=False)
    team_name = Column(String(150), nullable=True) # alias for name
    college = Column(String(150), default="Riverdale College of Technology", index=True)
    tagline = Column(String(255), default="")
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    pitch = Column(Text, default="")
    team_description = Column(Text, default="")
    collaboration_preference = Column(String(255), default="")

    # Core data fields matching teams.csv
    current_members_json = Column(Text, default="[]")       # List of student_ids: ["S0966", "S0597"]
    current_team_size = Column(Integer, default=1)
    vacancies = Column(Integer, default=3, index=True)      # Open only while vacancies > 0
    current_skills_json = Column(Text, default="{}")        # Dict skill -> level: {"IoT": 3}
    required_skills_json = Column(Text, default="[]")       # List of skills: ["Cloud Computing"]
    preferred_skills_json = Column(Text, default="[]")      # List of skills: ["Data Analysis"]
    skill_requirements_json = Column(Text, default="{}")    # Dict skill -> MIN level: {"Cloud Computing": 5}
    interests_json = Column(Text, default="[]")             # List of strings
    preferred_experience = Column(String(50), default="Intermediate", index=True) # Beginner, Intermediate, Advanced
    availability = Column(String(50), default="Full-time", index=True)            # Full-time, Part-time, Weekends
    preferred_roles_json = Column(Text, default="[]")       # List of strings

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("Event", back_populates="teams")
    leader = relationship("User", back_populates="teams_created", foreign_keys=[leader_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    open_seats = relationship("OpenSeat", back_populates="team", cascade="all, delete-orphan")
    messages = relationship("TeamMessage", back_populates="team", cascade="all, delete-orphan")
    join_requests = relationship("TeamJoinRequest", back_populates="team", cascade="all, delete-orphan")

    @property
    def current_members(self):
        try:
            return json.loads(self.current_members_json) if self.current_members_json else []
        except Exception:
            return []

    @current_members.setter
    def current_members(self, val):
        self.current_members_json = json.dumps(val if isinstance(val, list) else [])
        self.current_team_size = len(val) if isinstance(val, list) else 0

    @property
    def current_skills(self):
        try:
            return json.loads(self.current_skills_json) if self.current_skills_json else {}
        except Exception:
            return {}

    @current_skills.setter
    def current_skills(self, val):
        self.current_skills_json = json.dumps(val if isinstance(val, dict) else {})

    @property
    def required_skills(self):
        try:
            return json.loads(self.required_skills_json) if self.required_skills_json else []
        except Exception:
            return []

    @required_skills.setter
    def required_skills(self, val):
        self.required_skills_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def preferred_skills(self):
        try:
            return json.loads(self.preferred_skills_json) if self.preferred_skills_json else []
        except Exception:
            return []

    @preferred_skills.setter
    def preferred_skills(self, val):
        self.preferred_skills_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def skill_requirements(self):
        try:
            return json.loads(self.skill_requirements_json) if self.skill_requirements_json else {}
        except Exception:
            return {}

    @skill_requirements.setter
    def skill_requirements(self, val):
        self.skill_requirements_json = json.dumps(val if isinstance(val, dict) else {})

    @property
    def interests(self):
        try:
            return json.loads(self.interests_json) if self.interests_json else []
        except Exception:
            return []

    @interests.setter
    def interests(self, val):
        self.interests_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def preferred_roles(self):
        try:
            return json.loads(self.preferred_roles_json) if self.preferred_roles_json else []
        except Exception:
            return []

    @preferred_roles.setter
    def preferred_roles(self, val):
        self.preferred_roles_json = json.dumps(val if isinstance(val, list) else [])


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(100), default="Member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="memberships")


class TeamJoinRequest(Base):
    __tablename__ = "team_join_requests"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(String(50), nullable=True, index=True)
    message = Column(Text, default="Interested in joining this team!")
    status = Column(String(50), default="pending", index=True) # pending, accepted, declined
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="join_requests")
    user = relationship("User", back_populates="join_requests")


class OpenSeat(Base):
    __tablename__ = "open_seats"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    role_title = Column(String(100), nullable=False)
    required_skills_json = Column(Text, default="[]")
    short_note = Column(Text, default="")
    status = Column(String(50), default="open") # open, filled, closed
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="open_seats")
    event = relationship("Event", back_populates="open_seats")
    applications = relationship("SeatApplication", back_populates="seat", cascade="all, delete-orphan")

    @property
    def required_skills(self):
        try:
            return json.loads(self.required_skills_json) if self.required_skills_json else []
        except Exception:
            return []

    @required_skills.setter
    def required_skills(self, val):
        self.required_skills_json = json.dumps(val if isinstance(val, list) else [])


class SeatApplication(Base):
    __tablename__ = "seat_applications"

    id = Column(Integer, primary_key=True, index=True)
    seat_id = Column(Integer, ForeignKey("open_seats.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, default="")
    status = Column(String(50), default="pending") # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    seat = relationship("OpenSeat", back_populates="applications")
    user = relationship("User")


class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    message = Column(Text, default="")
    proposed_role = Column(String(100), default="Member")
    status = Column(String(50), default="pending") # pending, accepted, declined
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="sent_invites", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_invites", foreign_keys=[receiver_id])
    team = relationship("Team")
    event = relationship("Event")


class TeamMessage(Base):
    __tablename__ = "team_messages"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False) # 1 to 5
    tags_json = Column(Text, default="[]")   # ["Reliable", "Great communicator"]
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def tags(self):
        try:
            return json.loads(self.tags_json) if self.tags_json else []
        except Exception:
            return []

    @tags.setter
    def tags(self, val):
        self.tags_json = json.dumps(val if isinstance(val, list) else [])


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(100), nullable=False)
    details = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
