import math
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, TeamMember, Event, User, TeamMessage, TeamJoinRequest, generate_next_team_id
from app.auth import get_current_user, get_current_user_optional
from app.schemas import (
    TeamCreate, TeamUpdate, TeamResponse, TeamMemberResponse,
    TeamGapAnalysisResponse, TeamMessageCreate, TeamMessageResponse,
    UserPublicResponse, PaginatedTeamsResponse,
    TeamJoinRequestCreate, TeamJoinRequestResponse,
    RecommendedTeamResponse, RecommendedStudentResponse
)
from app.gap_analyzer import analyze_team_gaps
from matching import get_matcher

router = APIRouter(prefix="/api/teams", tags=["Teams"])
recommended_router = APIRouter(prefix="/api/me", tags=["Recommendations"])

def _build_team_response(team: Team, match_res: Optional[Any] = None) -> TeamResponse:
    members_res = []
    for m in (team.members or []):
        members_res.append(TeamMemberResponse(
            id=m.id,
            user_id=m.user_id,
            student_id=m.user.student_id if m.user else None,
            user=UserPublicResponse.from_orm(m.user) if m.user else None,
            role=m.role,
            joined_at=m.joined_at
        ))
    return TeamResponse(
        id=team.id,
        team_id=team.team_id,
        team_name=team.team_name or team.name,
        name=team.name,
        college=team.college or "",
        current_members=team.current_members or [],
        current_team_size=team.current_team_size or len(team.current_members or []),
        vacancies=team.vacancies,
        current_skills=team.current_skills or {},
        required_skills=team.required_skills or [],
        preferred_skills=team.preferred_skills or [],
        skill_requirements=team.skill_requirements or {},
        interests=team.interests or [],
        preferred_experience=team.preferred_experience or "Intermediate",
        availability=team.availability or "Full-time",
        preferred_roles=team.preferred_roles or [],
        team_description=team.team_description or "",
        tagline=team.tagline or "",
        collaboration_preference=team.collaboration_preference or "",
        leader_id=team.leader_id,
        pitch=team.pitch or "",
        event_id=team.event_id,
        event_name=team.event.name if team.event else None,
        members=members_res,
        created_at=team.created_at,
        match_score=match_res.score if match_res else None,
        match_reasons=match_res.reasons if match_res else None,
        match_breakdown=match_res.breakdown if match_res else None,
        engine=match_res.engine if match_res else None
    )

@router.get("", response_model=List[TeamResponse])
def get_teams(
    event_id: Optional[int] = None,
    search: Optional[str] = None,
    my_teams_only: Optional[bool] = False,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Team listing endpoint with search and optional auth."""
    query = db.query(Team)

    if event_id:
        query = query.filter(Team.event_id == event_id)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            Team.name.ilike(s) |
            Team.team_name.ilike(s) |
            Team.tagline.ilike(s) |
            Team.college.ilike(s) |
            Team.team_description.ilike(s)
        )

    if my_teams_only:
        if not current_user:
            return []
        team_ids = [m.team_id for m in current_user.memberships]
        query = query.filter(Team.id.in_(team_ids))

    teams = query.order_by(Team.created_at.desc()).limit(100).all()

    match_map = {}
    if current_user:
        try:
            matcher = get_matcher()
            m_res = matcher.match_student_to_teams(current_user, teams)
            match_map = {r.team_id: r for r in m_res}
        except Exception as e:
            print(f"[Matcher Warning] {e}")

    return [_build_team_response(t, match_map.get(t.id)) for t in teams]

@router.get("/browse", response_model=PaginatedTeamsResponse)
def browse_teams(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    college: Optional[str] = None,
    skill: Optional[str] = None,
    interest: Optional[str] = None,
    role: Optional[str] = None,
    availability: Optional[str] = None,
    experience: Optional[str] = None,
    vacancies_gt_0: Optional[bool] = True,
    sort_by: Optional[str] = Query("best_match", description="best_match, vacancies, newest"),
    min_match_pct: Optional[int] = Query(None, ge=0, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Browse teams with live complement match scoring, filters, and pagination."""
    query = db.query(Team)

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            Team.name.ilike(s) |
            Team.team_name.ilike(s) |
            Team.tagline.ilike(s) |
            Team.college.ilike(s) |
            Team.team_description.ilike(s)
        )
    if college:
        query = query.filter(Team.college.ilike(f"%{college}%"))
    if availability:
        query = query.filter(Team.availability == availability)
    if experience:
        query = query.filter(Team.preferred_experience == experience)
    if skill:
        query = query.filter(
            Team.required_skills_json.ilike(f"%{skill}%") |
            Team.preferred_skills_json.ilike(f"%{skill}%")
        )
    if interest:
        query = query.filter(Team.interests_json.ilike(f"%{interest}%"))
    if role:
        query = query.filter(Team.preferred_roles_json.ilike(f"%{role}%"))
    if vacancies_gt_0:
        query = query.filter(Team.vacancies > 0)

    teams = query.all()

    # Compute complement matches for current user
    match_map = {}
    if current_user:
        try:
            matcher = get_matcher()
            m_res = matcher.match_student_to_teams(current_user, teams)
            match_map = {r.team_id: r for r in m_res}
        except Exception as e:
            print(f"[Matcher Warning] {e}")

    # Min match filter if provided
    if min_match_pct is not None and current_user:
        teams = [t for t in teams if (match_map.get(t.id).score if match_map.get(t.id) else 0) >= min_match_pct]

    # Sort logic
    if sort_by == "best_match" and current_user:
        teams.sort(key=lambda t: match_map.get(t.id).score if match_map.get(t.id) else 0, reverse=True)
    elif sort_by == "newest":
        teams.sort(key=lambda t: t.created_at, reverse=True)
    else:  # vacancies
        teams.sort(key=lambda t: (t.vacancies or 0, t.created_at), reverse=True)

    total = len(teams)
    start = (page - 1) * per_page
    end = start + per_page
    page_teams = teams[start:end]
    pages = max(1, math.ceil(total / per_page))

    items = [_build_team_response(t, match_map.get(t.id)) for t in page_teams]
    return PaginatedTeamsResponse(items=items, total=total, page=page, pages=pages)

@router.post("", response_model=TeamResponse)
def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team_name = data.team_name.strip()
    college = data.college or current_user.college or "University"
    
    # Safe sequential team ID (e.g. T301)
    next_team_id = generate_next_team_id(db)

    new_team = Team(
        team_id=next_team_id,
        event_id=data.event_id or 1,
        name=team_name,
        team_name=team_name,
        college=college,
        leader_id=current_user.id,
        tagline="Innovating together",
        team_description=data.team_description or "",
        collaboration_preference=data.collaboration_preference or current_user.collaboration_preference or "",
        vacancies=max(1, data.vacancies if data.vacancies is not None else 3),
        preferred_experience=data.preferred_experience or "Intermediate",
        availability=data.availability or "Full-time",
        current_team_size=1
    )
    new_team.required_skills = data.required_skills or []
    new_team.preferred_skills = data.preferred_skills or []
    new_team.skill_requirements = data.skill_requirements or {s: 3 for s in (data.required_skills or [])}
    new_team.interests = data.interests or []
    new_team.preferred_roles = data.preferred_roles or []

    # Leader initial membership and skills
    leader_student_id = current_user.student_id or f"S{current_user.id:04d}"
    new_team.current_members = [leader_student_id]
    new_team.current_skills = current_user.skill_proficiency or {}

    db.add(new_team)
    db.flush()

    leader_member = TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role="Team Lead"
    )
    db.add(leader_member)
    db.commit()
    db.refresh(new_team)

    return _build_team_response(new_team)

@router.get("/{team_id}", response_model=TeamResponse)
def get_team_detail(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return _build_team_response(team)

@router.put("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team leader can modify team")

    if data.team_name is not None:
        team.name = data.team_name.strip()
        team.team_name = data.team_name.strip()
    if data.required_skills is not None:
        team.required_skills = data.required_skills
    if data.preferred_skills is not None:
        team.preferred_skills = data.preferred_skills
    if data.skill_requirements is not None:
        team.skill_requirements = data.skill_requirements
    if data.interests is not None:
        team.interests = data.interests
    if data.preferred_experience is not None:
        team.preferred_experience = data.preferred_experience
    if data.availability is not None:
        team.availability = data.availability
    if data.preferred_roles is not None:
        team.preferred_roles = data.preferred_roles
    if data.team_description is not None:
        team.team_description = data.team_description
    if data.collaboration_preference is not None:
        team.collaboration_preference = data.collaboration_preference
    if data.vacancies is not None:
        team.vacancies = max(0, data.vacancies)

    db.commit()
    db.refresh(team)
    return _build_team_response(team)

@router.get("/{team_id}/gaps", response_model=TeamGapAnalysisResponse)
def get_team_gap_analysis(
    team_id: int,
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return analyze_team_gaps(team, team.event, db)

@router.post("/{team_id}/join-request", response_model=TeamJoinRequestResponse)
def create_join_request(
    team_id: int,
    data: TeamJoinRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.vacancies <= 0:
        raise HTTPException(status_code=400, detail="Team has no vacancies")

    existing = db.query(TeamJoinRequest).filter(
        TeamJoinRequest.team_id == team_id,
        TeamJoinRequest.user_id == current_user.id,
        TeamJoinRequest.status == "pending"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request for this team")

    already_member = any(m.user_id == current_user.id for m in (team.members or []))
    if already_member:
        raise HTTPException(status_code=400, detail="You are already a member of this team")

    jr = TeamJoinRequest(
        team_id=team_id,
        user_id=current_user.id,
        student_id=current_user.student_id,
        message=data.message or "Interested in joining your team!",
        status="pending"
    )
    db.add(jr)
    db.commit()
    db.refresh(jr)

    return TeamJoinRequestResponse(
        id=jr.id,
        team_id=jr.team_id,
        team_name=team.team_name or team.name,
        user_id=jr.user_id,
        student_id=jr.student_id,
        student_name=current_user.name,
        student_avatar=current_user.avatar_url or "",
        message=jr.message,
        status=jr.status,
        created_at=jr.created_at,
    )

@router.get("/{team_id}/join-requests", response_model=List[TeamJoinRequestResponse])
def get_team_join_requests(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    is_member = any(m.user_id == current_user.id for m in (team.members or []))
    if team.leader_id != current_user.id and not is_member:
        raise HTTPException(status_code=403, detail="Only team members can view join requests")

    requests = db.query(TeamJoinRequest).filter(
        TeamJoinRequest.team_id == team_id
    ).order_by(TeamJoinRequest.created_at.desc()).all()

    return [
        TeamJoinRequestResponse(
            id=jr.id,
            team_id=jr.team_id,
            team_name=team.team_name or team.name,
            user_id=jr.user_id,
            student_id=jr.student_id,
            student_name=jr.user.name if jr.user else "Applicant",
            student_avatar=jr.user.avatar_url if jr.user else "",
            message=jr.message,
            status=jr.status,
            created_at=jr.created_at,
        )
        for jr in requests
    ]

@router.get("/{team_id}/recommended-students")
def get_recommended_students(
    team_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    is_member = any(m.user_id == current_user.id for m in (team.members or []))
    if team.leader_id != current_user.id and not is_member:
        raise HTTPException(status_code=403, detail="Only team members can view recommended candidates")

    all_students = db.query(User).filter(User.student_id.isnot(None)).limit(300).all()

    matcher = get_matcher()
    match_results = matcher.match_team_to_students(team, all_students)

    total = len(match_results)
    start = (page - 1) * per_page
    page_results = match_results[start:start + per_page]
    pages = max(1, math.ceil(total / per_page))

    student_lookup = {s.id: s for s in all_students}
    items = []
    for res in page_results:
        student = student_lookup.get(res.user_id)
        if not student:
            continue
        items.append({
            "id": student.id,
            "student_id": student.student_id,
            "score": res.score,
            "reasons": res.reasons,
            "complementary_skills": res.complementary_skills,
            "shared_interests": res.shared_interests,
            "missing_skills_covered": res.missing_skills_covered,
            "notes": res.notes,
            "student": UserPublicResponse.from_orm(student).dict()
        })

    return {"items": items, "total": total, "page": page, "pages": pages}

@router.post("/{team_id}/messages", response_model=TeamMessageResponse)
def send_team_message(
    team_id: int,
    data: TeamMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    is_member = any(m.user_id == current_user.id for m in team.members)
    if not is_member and team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="You must be a member of this team to chat")

    msg = TeamMessage(
        team_id=team_id,
        sender_id=current_user.id,
        content=data.content.strip()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return TeamMessageResponse(
        id=msg.id,
        team_id=msg.team_id,
        sender_id=msg.sender_id,
        sender_name=current_user.name,
        sender_avatar=current_user.avatar_url,
        content=msg.content,
        created_at=msg.created_at
    )

@router.get("/{team_id}/messages", response_model=List[TeamMessageResponse])
def get_team_messages(
    team_id: int,
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    is_member = any(m.user_id == current_user.id for m in team.members)
    if not is_member and team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="You must be a member of this team to view chat")

    messages = db.query(TeamMessage).filter(TeamMessage.team_id == team_id).order_by(TeamMessage.created_at.asc()).limit(limit).all()

    return [
        TeamMessageResponse(
            id=m.id,
            team_id=m.team_id,
            sender_id=m.sender_id,
            sender_name=m.sender.name if m.sender else "Member",
            sender_avatar=m.sender.avatar_url if m.sender else "",
            content=m.content,
            created_at=m.created_at
        )
        for m in messages
    ]

# Recommended teams for current user (student -> teams matching)
@recommended_router.get("/recommended-teams")
def get_recommended_teams(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Exclude teams user already belongs to
    my_team_ids = {m.team_id for m in current_user.memberships}
    if current_user.teams_created:
        my_team_ids.update(t.id for t in current_user.teams_created)

    query = db.query(Team).filter(Team.vacancies > 0)
    if my_team_ids:
        query = query.filter(~Team.id.in_(my_team_ids))

    all_teams = query.all()
    if not all_teams:
        return {"items": [], "total": 0, "page": page, "pages": 1, "engine": "Rule-based engine"}

    matcher = get_matcher()
    match_results = matcher.match_student_to_teams(current_user, all_teams)

    team_lookup = {t.id: t for t in all_teams}
    total = len(match_results)
    start = (page - 1) * per_page
    page_results = match_results[start:start + per_page]

    engine_name = "Rule-based engine"
    items = []
    for res in page_results:
        team = team_lookup.get(res.team_id)
        if not team:
            continue
        engine_name = getattr(res, "engine", "Rule-based engine")
        items.append({
            "id": team.id,
            "team_id": team.team_id,
            "score": res.score,
            "reasons": res.reasons,
            "complementary_skills": res.complementary_skills,
            "shared_interests": res.shared_interests,
            "missing_skills_covered": res.missing_skills_covered,
            "notes": res.notes,
            "breakdown": getattr(res, "breakdown", {}),
            "engine": engine_name,
            "team": _build_team_response(team, res).dict()
        })

    pages = max(1, math.ceil(total / per_page))
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "engine": engine_name
    }


debug_router = APIRouter(prefix="/api/debug", tags=["Debug"])

@debug_router.get("/recommendations")
def debug_recommendations(
    student_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Admin debug endpoint to inspect feature vector, schema alignment, and score breakdown."""
    target_student = current_user
    if student_id:
        try:
            sid_int = int(student_id)
            target_student = db.query(User).filter(User.id == sid_int).first() or current_user
        except ValueError:
            target_student = db.query(User).filter(User.student_id == student_id).first() or current_user

    first_team = db.query(Team).filter(Team.vacancies > 0).first()
    if not first_team:
        return {"error": "No teams found"}

    from matching.features import build_features
    features = build_features(target_student, first_team)
    matcher = get_matcher()
    results = matcher.match_student_to_teams(target_student, [first_team])
    res = results[0] if results else None

    import json
    from pathlib import Path
    schema_path = Path("models/feature_schema.json")
    schema_features = []
    if schema_path.exists():
        try:
            schema_data = json.load(open(schema_path))
            schema_features = schema_data.get("feature_names", [])
        except Exception:
            pass

    return {
        "student": {
            "id": target_student.id,
            "student_id": target_student.student_id,
            "name": target_student.name,
            "skills": target_student.skills,
            "skill_proficiency": target_student.skill_proficiency,
            "interests": target_student.interests
        },
        "sample_team": {
            "id": first_team.id,
            "team_id": first_team.team_id,
            "name": first_team.name,
            "required_skills": first_team.required_skills,
            "skill_requirements": first_team.skill_requirements
        },
        "engine": getattr(res, "engine", getattr(matcher, "__class__", type(matcher)).__name__),
        "features_count": len(features),
        "schema_features_count": len(schema_features),
        "schema_matches_exact": len(features) == len(schema_features),
        "score": res.score if res else 0,
        "breakdown": getattr(res, "breakdown", {}) if res else {},
        "reasons": res.reasons if res else [],
        "feature_vector_sample": features[:20]
    }
