from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    name = Column(String(100), nullable=False)
    college = Column(String(150), nullable=False)
    city = Column(String(100), default="Delhi")
    year = Column(String(50), default="3rd Year")
    short_bio = Column(Text, default="")
    avatar_url = Column(String(255), default="")

    # JSON stored fields (stored as JSON string or native JSON in SQLite)
    skills_json = Column(Text, default="[]")       # List of {"name": "Python", "level": "Advanced"}
    interests_json = Column(Text, default="[]")    # List of strings e.g. ["AI & ML", "FinTech"]
    blocked_users_json = Column(Text, default="[]")# List of user IDs

    experience_level = Column(String(50), default="Intermediate") # Beginner, Intermediate, Advanced
    past_hackathons_count = Column(Integer, default=0)
    github_url = Column(String(255), default="")
    linkedin_url = Column(String(255), default="")
    
    # Matching attributes
    availability = Column(String(50), default="Weekends") # Weekdays, Weekends, Evenings, Full-time / Flexible
    goal = Column(String(50), default="Win Grand Prize") # Win Grand Prize, Learn & Build Skills, Network & Have Fun
    
    # Work style
    work_schedule = Column(String(50), default="Night Owl") # Early Bird, Night Owl, Flexible
    work_role = Column(String(50), default="Executor / Builder") # Leader / Coordinator, Executor / Builder, Strategist / Ideator
    work_vibe = Column(String(50), default="Competitive / Serious") # Competitive / Serious, Balanced, Casual / Experimental

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

    @property
    def skills(self):
        try:
            return json.loads(self.skills_json) if self.skills_json else []
        except Exception:
            return []

    @skills.setter
    def skills(self, val):
        self.skills_json = json.dumps(val)

    @property
    def interests(self):
        try:
            return json.loads(self.interests_json) if self.interests_json else []
        except Exception:
            return []

    @interests.setter
    def interests(self, val):
        self.interests_json = json.dumps(val)

    @property
    def blocked_users(self):
        try:
            return json.loads(self.blocked_users_json) if self.blocked_users_json else []
        except Exception:
            return []

    @blocked_users.setter
    def blocked_users(self, val):
        self.blocked_users_json = json.dumps(val)


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
        self.required_roles_json = json.dumps(val)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String(100), nullable=False)
    tagline = Column(String(255), default="")
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pitch = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="teams")
    leader = relationship("User", back_populates="teams_created", foreign_keys=[leader_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    open_seats = relationship("OpenSeat", back_populates="team", cascade="all, delete-orphan")
    messages = relationship("TeamMessage", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(100), default="Member")
    joined_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="memberships")


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
        self.required_skills_json = json.dumps(val)


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
        self.tags_json = json.dumps(val)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(100), nullable=False)
    details = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
