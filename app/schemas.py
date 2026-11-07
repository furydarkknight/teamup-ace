from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# --- Meta Categories ---
class CategoriesMetaResponse(BaseModel):
    skills: List[str]
    skill_groups: Dict[str, List[str]]
    proficiency_levels: List[int]
    proficiency_labels: Dict[int, str]
    interests: List[str]
    experience_levels: List[str]
    availability: List[str]
    preferred_team_sizes: List[int]
    preferred_roles: List[str]
    collaboration_preferences: List[str]
    colleges: List[str]

# --- Auth & User Schemas ---
class SignUpRequest(BaseModel):
    email: str
    password: str
    name: str
    college: str
    city: Optional[str] = "Delhi"
    year: Optional[str] = "3rd Year"
    skills: Optional[List[str]] = None
    skill_proficiency: Optional[Dict[str, int]] = None
    interests: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    experience_level: Optional[str] = "Intermediate"
    availability: Optional[str] = "Full-time"
    preferred_team_size: Optional[int] = 4
    collaboration_preference: Optional[str] = ""
    bio: Optional[str] = ""
    project_experience: Optional[List[str]] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class UserPublicResponse(BaseModel):
    id: int
    student_id: Optional[str] = None
    name: str
    college: str
    city: Optional[str] = "Delhi"
    year: Optional[str] = "3rd Year"
    short_bio: Optional[str] = ""
    bio: Optional[str] = ""
    avatar_url: str
    is_verified: bool
    skills: List[str]
    skill_proficiency: Dict[str, int] = {}
    skills_items: Optional[List[Dict[str, Any]]] = []
    interests: List[str]
    experience_level: str
    project_experience: List[str] = []
    preferred_roles: List[str] = []
    availability: str
    preferred_team_size: int = 4
    collaboration_preference: str = ""
    past_hackathons_count: int = 0
    github_url: Optional[str] = ""
    linkedin_url: Optional[str] = ""
    is_mentor: bool = False
    seeking_mentor: bool = False
    reliability_score: float = 0.0
    ratings_count: int = 0
    match_score: Optional[int] = None
    match_reasons: Optional[List[str]] = None
    missing_skills_covered: Optional[List[str]] = None
    match_breakdown: Optional[Dict[str, Any]] = None
    engine: Optional[str] = None

    class Config:
        from_attributes = True

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    college: Optional[str] = None
    city: Optional[str] = None
    year: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    skills: Optional[List[str]] = None
    skill_proficiency: Optional[Dict[str, int]] = None
    interests: Optional[List[str]] = None
    experience_level: Optional[str] = None
    project_experience: Optional[List[str]] = None
    preferred_roles: Optional[List[str]] = None
    availability: Optional[str] = None
    preferred_team_size: Optional[int] = None
    collaboration_preference: Optional[str] = None
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

# --- Team Schemas ---
class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    student_id: Optional[str] = None
    user: Optional[UserPublicResponse] = None
    role: str
    joined_at: datetime

class TeamResponse(BaseModel):
    id: int
    team_id: Optional[str] = None
    team_name: str
    name: Optional[str] = None
    college: str
    current_members: List[str] = []
    current_team_size: int = 1
    vacancies: int = 3
    current_skills: Dict[str, int] = {}
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    skill_requirements: Dict[str, int] = {}
    interests: List[str] = []
    preferred_experience: str = "Intermediate"
    availability: str = "Full-time"
    preferred_roles: List[str] = []
    team_description: Optional[str] = ""
    tagline: Optional[str] = ""
    collaboration_preference: Optional[str] = ""
    leader_id: Optional[int] = None
    pitch: Optional[str] = ""
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    members: List[TeamMemberResponse] = []
    created_at: datetime
    match_score: Optional[int] = None
    match_reasons: Optional[List[str]] = None
    match_breakdown: Optional[Dict[str, Any]] = None
    engine: Optional[str] = None

    class Config:
        from_attributes = True

class TeamCreate(BaseModel):
    team_name: str
    college: Optional[str] = None
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []
    skill_requirements: Optional[Dict[str, int]] = None
    interests: Optional[List[str]] = []
    preferred_experience: Optional[str] = "Intermediate"
    availability: Optional[str] = "Full-time"
    preferred_roles: Optional[List[str]] = []
    team_description: Optional[str] = ""
    collaboration_preference: Optional[str] = ""
    vacancies: Optional[int] = 3
    event_id: Optional[int] = 1

class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    skill_requirements: Optional[Dict[str, int]] = None
    interests: Optional[List[str]] = None
    preferred_experience: Optional[str] = None
    availability: Optional[str] = None
    preferred_roles: Optional[List[str]] = None
    team_description: Optional[str] = None
    collaboration_preference: Optional[str] = None
    vacancies: Optional[int] = None

# --- Join Requests ---
class TeamJoinRequestCreate(BaseModel):
    message: Optional[str] = "Interested in joining your team!"

class TeamJoinRequestResponse(BaseModel):
    id: int
    team_id: int
    team_name: str
    user_id: int
    student_id: Optional[str] = None
    student_name: str
    student_avatar: str
    message: str
    status: str
    created_at: datetime

class JoinRequestUpdateStatus(BaseModel):
    status: str # "accepted" or "declined"

# --- Recommendations / Matches ---
class RecommendedTeamResponse(BaseModel):
    id: int
    team_id: Optional[str] = None
    score: int
    reasons: List[str]
    complementary_skills: List[str]
    shared_interests: List[str]
    missing_skills_covered: List[str]
    team: TeamResponse

class RecommendedStudentResponse(BaseModel):
    id: int
    student_id: Optional[str] = None
    score: int
    reasons: List[str]
    complementary_skills: List[str]
    shared_interests: List[str]
    missing_skills_covered: List[str]
    student: UserPublicResponse

# Existing event match response
class MatchResultResponse(BaseModel):
    user_id: int
    user: UserPublicResponse
    score: int # 0-100
    reasons: List[str]
    complementary_skills: List[str]
    shared_interests: List[str]
    missing_skills_covered: Optional[List[str]] = []
    workstyle_compatibility: int = 75
    is_mentor_match: bool = False
    notes: Optional[str] = None

# --- Open Seats & Applications ---
class OpenSeatCreate(BaseModel):
    team_id: int
    event_id: int
    role_title: str
    required_skills: List[str]
    short_note: Optional[str] = ""

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

class SeatApplicationResponse(BaseModel):
    id: int
    user_id: int
    user: UserPublicResponse
    note: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Invites ---
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

# --- Team Chat & Gap Analysis ---
class TeamGapCandidate(BaseModel):
    role: str
    user: UserPublicResponse
    score: int
    reason: str

class TeamGapAnalysisResponse(BaseModel):
    team_id: int
    event_id: Optional[int] = None
    required_skills: List[str]
    skill_requirements: Dict[str, int]
    current_skills: Dict[str, int]
    missing_skills: List[str]
    covered_skills: List[str]
    skill_comparison: List[Dict[str, Any]]
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

# --- Feedback & Safety ---
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

# --- Pagination Wrappers ---
class PaginatedTeamsResponse(BaseModel):
    items: List[TeamResponse]
    total: int
    page: int
    pages: int

class PaginatedStudentsResponse(BaseModel):
    items: List[UserPublicResponse]
    total: int
    page: int
    pages: int
