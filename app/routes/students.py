from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Team
from app.auth import get_current_user
from app.schemas import UserPublicResponse, PaginatedStudentsResponse

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("", response_model=PaginatedStudentsResponse)
def browse_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    college: Optional[str] = None,
    skill: Optional[str] = None,
    interest: Optional[str] = None,
    role: Optional[str] = None,
    availability: Optional[str] = None,
    experience: Optional[str] = None,
    fills_gap_for_team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Browse all students with filters.
    fills_gap_for_team_id: when provided, boosts students whose skills cover the team's required_skills gaps.
    """
    query = db.query(User)

    if college:
        query = query.filter(User.college.ilike(f"%{college}%"))
    if availability:
        query = query.filter(User.availability == availability)
    if experience:
        query = query.filter(User.experience_level == experience)
    if skill:
        query = query.filter(User.skills_json.ilike(f"%{skill}%"))
    if interest:
        query = query.filter(User.interests_json.ilike(f"%{interest}%"))
    if role:
        query = query.filter(User.preferred_roles_json.ilike(f"%{role}%"))

    blocked = set(current_user.blocked_users or [])
    users = query.order_by(User.reliability_score.desc(), User.id.asc()).all()

    users = [u for u in users if u.id not in blocked and u.id != current_user.id]

    if fills_gap_for_team_id:
        team = db.query(Team).filter(Team.id == fills_gap_for_team_id).first()
        if team:
            required = set(s.lower() for s in (team.required_skills or []))
            current_team_skills = set(s.lower() for s in (team.current_skills or {}).keys())
            gap_skills = required - current_team_skills

            def gap_score(u: User):
                u_skills = set(s.lower() for s in (u.skills or []))
                return len(u_skills & gap_skills)

            users = sorted(users, key=gap_score, reverse=True)

    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page
    page_users = users[start:end]

    items = [UserPublicResponse.from_orm(u) for u in page_users]
    pages = max(1, (total + per_page - 1) // per_page)

    return PaginatedStudentsResponse(items=items, total=total, page=page, pages=pages)


@router.get("/{student_id_or_int}", response_model=UserPublicResponse)
def get_student(
    student_id_or_int: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a student by DB id (integer) or student_id string (e.g. S0001)."""
    try:
        db_id = int(student_id_or_int)
        user = db.query(User).filter(User.id == db_id).first()
    except ValueError:
        user = db.query(User).filter(User.student_id == student_id_or_int).first()

    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    return UserPublicResponse.from_orm(user)
