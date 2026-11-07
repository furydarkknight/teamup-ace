from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# --- Auth & User Schemas ---
class SignUpRequest(BaseModel):
    email: str
    password: str
    name: str
    college: str
    city: Optional[str] = "Delhi"
    year: Optional[str] = "3rd Year"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class SkillItem(BaseModel):
    name: str
    level: str = "Intermediate" # Beginner, Intermediate, Advanced

class UserPublicResponse(BaseModel):
    id: int
    name: str
    college: str
    city: str
    year: str
    short_bio: str
    avatar_url: str
    is_verified: bool
    skills: List[Dict[str, Any]]
    interests: List[str]
    experience_level: str
    past_hackathons_count: int
    github_url: str
    linkedin_url: str
    availability: str
    goal: str
    work_schedule: str
    work_role: str
    work_vibe: str
    is_mentor: bool
    seeking_mentor: bool
    reliability_score: float
    ratings_count: int

    class Config:
        from_attributes = True

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    college: Optional[str] = None
    city: Optional[str] = None
    year: Optional[str] = None
    short_bio: Optional[str] = None
    avatar_url: Optional[str] = None
    skills: Optional[List[Dict[str, Any]]] = None
    interests: Optional[List[str]] = None
    experience_level: Optional[str] = None
    past_hackathons_count: Optional[int] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    availability: Optional[str] = None
    goal: Optional[str] = None
    work_schedule: Optional[str] = None
    work_role: Optional[str] = None
    work_vibe: Optional[str] = None
    is_mentor: Optional[bool] = None
    seeking_mentor: Optional[bool] = None

# --- Event Schemas ---
class EventResponse(BaseModel):
    id: int
    name: str
    tagline: str
    theme: str
    dates: str
    mode: str
    city_venue: str
    team_size_min: int
    team_size_max: int
    prize_pool: str
    description: str
    required_roles: List[str]
    banner_url: str
    teams_count: Optional[int] = 0
    open_seats_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- Matching Schemas ---
class MatchResultResponse(BaseModel):
    user_id: int
    user: UserPublicResponse
    score: int # 0-100
    reasons: List[str]
    complementary_skills: List[str]
    shared_interests: List[str]
    workstyle_compatibility: int # 0-100
    is_mentor_match: bool = False
    notes: Optional[str] = None

# --- Open Seats Schemas ---
class OpenSeatCreate(BaseModel):
    team_id: int
    event_id: int
    role_title: str
    required_skills: List[str]
    short_note: Optional[str] = ""

class SeatApplicationResponse(BaseModel):
    id: int
    user_id: int
    user: UserPublicResponse
    note: str
    status: str
    created_at: datetime

class OpenSeatResponse(BaseModel):
    id: int
    team_id: int
    team_name: str
    event_id: int
    role_title: str
    required_skills: List[str]
    short_note: str
    status: str
    created_at: datetime
    applications_count: int = 0
    leader_name: Optional[str] = ""

class SeatApplyRequest(BaseModel):
    note: Optional[str] = "I'd love to join your team for this role!"

# --- Invites Schemas ---
class InviteCreate(BaseModel):
    receiver_id: int
    event_id: int
    team_id: Optional[int] = None
    message: Optional[str] = "Hey, let's team up for this hackathon!"
    proposed_role: Optional[str] = "Teammate"

class InviteUpdateStatus(BaseModel):
    status: str # "accepted" or "declined"

class InviteResponse(BaseModel):
    id: int
    sender_id: int
    sender: UserPublicResponse
    receiver_id: int
    receiver: UserPublicResponse
    team_id: Optional[int]
    team_name: Optional[str]
    event_id: int
    event_name: Optional[str]
    message: str
    proposed_role: str
    status: str
    created_at: datetime

# --- Team Schemas ---
class TeamCreate(BaseModel):
    event_id: int
    name: str
    tagline: Optional[str] = ""
    pitch: Optional[str] = ""
    leader_role: Optional[str] = "Team Lead / Full Stack"

class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    user: UserPublicResponse
    role: str
    joined_at: datetime

class TeamResponse(BaseModel):
    id: int
    event_id: int
    event_name: str
    name: str
    tagline: str
    leader_id: int
    pitch: str
    members: List[TeamMemberResponse]
    created_at: datetime

class TeamGapCandidate(BaseModel):
    role: str
    user: UserPublicResponse
    score: int
    reason: str

class TeamGapAnalysisResponse(BaseModel):
    team_id: int
    event_id: int
    required_roles: List[str]
    covered_roles: List[str]
    missing_roles: List[str]
    suggested_role_split: Dict[str, str]
    ai_generated_pitch: str
    suggested_candidates: List[TeamGapCandidate]

class TeamMessageCreate(BaseModel):
    content: str

class TeamMessageResponse(BaseModel):
    id: int
    team_id: int
    sender_id: int
    sender_name: str
    sender_avatar: str
    content: str
    created_at: datetime

# --- Feedback & Safety Schemas ---
class FeedbackCreate(BaseModel):
    event_id: int
    team_id: int
    to_user_id: int
    rating: int # 1 to 5
    tags: List[str]
    comment: Optional[str] = ""

class ReportCreate(BaseModel):
    reported_user_id: int
    reason: str
    details: Optional[str] = ""

class BlockUserRequest(BaseModel):
    user_id: int
