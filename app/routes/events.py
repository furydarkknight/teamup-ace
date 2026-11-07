from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, User, Team, OpenSeat
from app.auth import get_current_user, get_current_user_optional
from app.schemas import EventResponse, MatchResultResponse, UserPublicResponse
from matching import get_matcher

router = APIRouter(prefix="/api/events", tags=["Events"])

@router.get("", response_model=List[EventResponse])
def list_events(
    search: Optional[str] = None,
    theme: Optional[str] = None,
    mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Event)

    if search:
        s = f"%{search}%"
        query = query.filter((Event.name.ilike(s)) | (Event.description.ilike(s)) | (Event.theme.ilike(s)))

    if theme and theme != "All":
        query = query.filter(Event.theme == theme)

    if mode and mode != "All":
        query = query.filter(Event.mode == mode)

    events = query.all()
    results = []

    for event in events:
        teams_count = db.query(Team).filter(Team.event_id == event.id).count()
        seats_count = db.query(OpenSeat).filter(
            OpenSeat.event_id == event.id,
            OpenSeat.status == "open"
        ).count()

        e_dict = {
            "id": event.id,
            "name": event.name,
            "tagline": event.tagline,
            "theme": event.theme,
            "dates": event.dates,
            "mode": event.mode,
            "city_venue": event.city_venue,
            "team_size_min": event.team_size_min,
            "team_size_max": event.team_size_max,
            "prize_pool": event.prize_pool,
            "description": event.description,
            "required_roles": event.required_roles,
            "banner_url": event.banner_url,
            "teams_count": teams_count,
            "open_seats_count": seats_count
        }
        results.append(EventResponse(**e_dict))

    return results

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    teams_count = db.query(Team).filter(Team.event_id == event.id).count()
    seats_count = db.query(OpenSeat).filter(
        OpenSeat.event_id == event.id,
        OpenSeat.status == "open"
    ).count()

    e_dict = {
        "id": event.id,
        "name": event.name,
        "tagline": event.tagline,
        "theme": event.theme,
        "dates": event.dates,
        "mode": event.mode,
        "city_venue": event.city_venue,
        "team_size_min": event.team_size_min,
        "team_size_max": event.team_size_max,
        "prize_pool": event.prize_pool,
        "description": event.description,
        "required_roles": event.required_roles,
        "banner_url": event.banner_url,
        "teams_count": teams_count,
        "open_seats_count": seats_count
    }
    return EventResponse(**e_dict)

@router.get("/{event_id}/matches", response_model=List[MatchResultResponse])
def get_event_matches(
    event_id: int,
    college: Optional[str] = None,
    city: Optional[str] = None,
    skill: Optional[str] = None,
    experience: Optional[str] = None,
    availability: Optional[str] = None,
    mentor_only: Optional[bool] = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Fetch candidate pool (exclude current user)
    cand_query = db.query(User).filter(User.id != current_user.id)

    if college and college != "All":
        cand_query = cand_query.filter(User.college == college)

    if city and city != "All":
        cand_query = cand_query.filter(User.city == city)

    if experience and experience != "All":
        cand_query = cand_query.filter(User.experience_level == experience)

    if availability and availability != "All":
        cand_query = cand_query.filter(User.availability == availability)

    if mentor_only:
        cand_query = cand_query.filter(User.is_mentor == True)

    candidates = cand_query.all()

    # Filter by specific skill if requested
    if skill and skill != "All":
        skill_lower = skill.lower()
        candidates = [
            c for c in candidates
            if any(skill_lower in s.get("name", "").lower() for s in c.skills)
        ]

    # Run modular matching engine (RuleBased or ML according to .env)
    matcher = get_matcher()
    match_results = matcher.match(current_user, event, candidates)

    # Build response format
    cand_map = {c.id: c for c in candidates}
    response_items: List[MatchResultResponse] = []

    for mr in match_results:
        cand_user = cand_map.get(mr.user_id)
        if not cand_user:
            continue

        response_items.append(MatchResultResponse(
            user_id=mr.user_id,
            user=UserPublicResponse.from_orm(cand_user),
            score=mr.score,
            reasons=mr.reasons,
            complementary_skills=mr.complementary_skills,
            shared_interests=mr.shared_interests,
            workstyle_compatibility=mr.workstyle_compatibility,
            is_mentor_match=mr.is_mentor_match,
            notes=mr.notes
        ))

    return response_items
