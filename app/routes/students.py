from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Team
from app.auth import get_current_user, get_current_user_optional
from app.schemas import UserPublicResponse, PaginatedStudentsResponse
from matching import get_matcher

router = APIRouter(prefix="/api/students", tags=["Students"])

@router.get("", response_model=PaginatedStudentsResponse)
@router.get("/browse", response_model=PaginatedStudentsResponse)
def browse_students(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    college: Optional[str] = None,
    skill: Optional[str] = None,
    interest: Optional[str] = None,
    role: Optional[str] = None,
    availability: Optional[str] = None,
    experience: Optional[str] = None,
    fills_gap_for_team_id: Optional[int] = None,
    sort_by: Optional[str] = Query("best_match", description="best_match, reliability, newest"),
    min_match_pct: Optional[int] = Query(None, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Browse all students with filters, team-scoped complement match percentages, and gap coverage.
    """
    query = db.query(User)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(User.name.ilike(s) | User.college.ilike(s) | User.skills_json.ilike(s))

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

    blocked = set(current_user.blocked_users or []) if current_user else set()
    current_uid = current_user.id if current_user else -1
    users = query.all()
    users = [u for u in users if u.id not in blocked and u.id != current_uid]

    # Resolve target team for match scoring
    target_team = None
    if fills_gap_for_team_id:
        target_team = db.query(Team).filter(Team.id == fills_gap_for_team_id).first()
    elif current_user and current_user.teams_created:
        target_team = current_user.teams_created[0]

    match_map = {}
    if target_team:
        try:
            matcher = get_matcher()
            m_res = matcher.match_team_to_students(target_team, users)
            match_map = {r.user_id: r for r in m_res}
        except Exception as e:
            print(f"[Matcher Warning] {e}")

    # Min match filter if provided
    if min_match_pct is not None and match_map:
        users = [u for u in users if (match_map.get(u.id).score if match_map.get(u.id) else 0) >= min_match_pct]

    # Sorting
    if sort_by == "best_match" and match_map:
        users.sort(key=lambda u: match_map.get(u.id).score if match_map.get(u.id) else 0, reverse=True)
    elif sort_by == "newest":
        users.sort(key=lambda u: u.id, reverse=True)
    else:  # reliability
        users.sort(key=lambda u: u.reliability_score or 0.0, reverse=True)

    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page
    page_users = users[start:end]

    items = []
    for u in page_users:
        resp = UserPublicResponse.from_orm(u)
        m = match_map.get(u.id)
        if m:
            resp.match_score = m.score
            resp.match_reasons = m.reasons
            resp.missing_skills_covered = m.missing_skills_covered
            resp.match_breakdown = getattr(m, "breakdown", {})
            resp.engine = getattr(m, "engine", "Rule-based engine")
        items.append(resp)

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
