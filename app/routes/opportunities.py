"""
Opportunities Hub API Routes (Phase 1)
Supports all 16 opportunity types, filters, search, detail view, registration, and bookmarking.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database import get_db
from app.auth import get_current_user_optional, get_current_user
from app.models import User, Event, Team
from app.models_expansion import Opportunity, Application, SavedItem

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities Hub"])


@router.get("")
def list_opportunities(
    type: Optional[str] = None,
    mode: Optional[str] = None,
    search: Optional[str] = None,
    skill: Optional[str] = None,
    status_filter: Optional[str] = None,
    sort: Optional[str] = Query("deadline", description="deadline, newest, popular"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Opportunity)

    if type and type != "All":
        query = query.filter(Opportunity.type == type)

    if mode and mode != "All":
        query = query.filter(Opportunity.location_mode == mode)

    if status_filter and status_filter != "All":
        query = query.filter(Opportunity.status == status_filter)

    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Opportunity.title.ilike(s),
                Opportunity.organizer_name.ilike(s),
                Opportunity.description.ilike(s),
                Opportunity.tags_json.ilike(s)
            )
        )

    if skill and skill != "All":
        query = query.filter(Opportunity.skills_json.ilike(f"%{skill}%"))

    if sort == "newest":
        query = query.order_by(desc(Opportunity.created_at))
    elif sort == "popular":
        query = query.order_by(desc(Opportunity.views_count), desc(Opportunity.is_featured))
    else:
        query = query.order_by(desc(Opportunity.is_featured), Opportunity.deadline)

    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "items": [
            {
                "id": o.id,
                "event_id": o.event_id,
                "title": o.title,
                "organizer_name": o.organizer_name,
                "type": o.type,
                "description": o.description,
                "eligibility": o.eligibility,
                "skills": o.skills,
                "location_mode": o.location_mode,
                "location_venue": o.location_venue,
                "start_date": o.start_date,
                "deadline": o.deadline,
                "team_size_min": o.team_size_min,
                "team_size_max": o.team_size_max,
                "prize_pool": o.prize_pool,
                "stipend_ctc": o.stipend_ctc,
                "banner_url": o.banner_url,
                "tags": o.tags,
                "status": o.status,
                "is_featured": o.is_featured,
                "views_count": o.views_count
            }
            for o in items
        ]
    }


@router.get("/types")
def get_opportunity_types(db: Session = Depends(get_db)):
    """Returns list of opportunity types with live counts"""
    all_types = [
        "Hackathon", "Competition", "Quiz", "Case Study", "Coding Challenge",
        "Workshop", "Webinar", "Conference", "Scholarship", "Fellowship",
        "Internship", "Full-time Job", "Part-time Job", "Freelance Project",
        "Mentorship Program", "Campus Ambassador Role"
    ]
    counts = {}
    for t in all_types:
        counts[t] = db.query(Opportunity).filter(Opportunity.type == t).count()
    return {"types": all_types, "counts": counts}


@router.get("/{id}")
def get_opportunity_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    opp = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    opp.views_count = (opp.views_count or 0) + 1
    db.commit()

    # Check if registered or saved by user
    is_registered = False
    is_saved = False
    if current_user:
        app_record = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.opportunity_id == opp.id
        ).first()
        is_registered = app_record is not None
        saved_record = db.query(SavedItem).filter(
            SavedItem.user_id == current_user.id,
            SavedItem.item_type == "opportunity",
            SavedItem.item_id == opp.id
        ).first()
        is_saved = saved_record is not None

    # Check teams formed for linked event
    teams_formed_count = 0
    if opp.event_id:
        teams_formed_count = db.query(Team).filter(Team.event_id == opp.event_id).count()

    return {
        "id": opp.id,
        "event_id": opp.event_id,
        "title": opp.title,
        "organizer_name": opp.organizer_name,
        "type": opp.type,
        "description": opp.description,
        "eligibility": opp.eligibility,
        "eligibility_year": opp.eligibility_year,
        "eligibility_branch": opp.eligibility_branch,
        "skills": opp.skills,
        "location_mode": opp.location_mode,
        "location_venue": opp.location_venue,
        "start_date": opp.start_date,
        "end_date": opp.end_date,
        "deadline": opp.deadline,
        "team_size_min": opp.team_size_min,
        "team_size_max": opp.team_size_max,
        "prize_pool": opp.prize_pool,
        "stipend_ctc": opp.stipend_ctc,
        "perks": opp.perks,
        "rounds": opp.rounds,
        "faqs": opp.faqs,
        "banner_url": opp.banner_url,
        "tags": opp.tags,
        "status": opp.status,
        "is_featured": opp.is_featured,
        "teams_formed_count": teams_formed_count,
        "is_registered": is_registered,
        "is_saved": is_saved
    }


@router.post("/{id}/register")
def register_for_opportunity(
    id: int,
    team_name: Optional[str] = None,
    cover_note: Optional[str] = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.opportunity_id == opp.id
    ).first()
    if existing:
        return {"message": "You are already registered for this opportunity", "status": existing.status}

    app_entry = Application(
        user_id=current_user.id,
        opportunity_id=opp.id,
        application_type="opportunity",
        status="Registered",
        cover_note=cover_note or "",
        status_timeline_json='[{"status": "Registered", "timestamp": "Just now", "note": "Registration successfully confirmed"}]'
    )
    db.add(app_entry)
    db.commit()

    return {
        "message": f"Successfully registered for {opp.title}!",
        "application_id": app_entry.id,
        "status": "Registered"
    }


@router.post("/{id}/save")
def toggle_save_opportunity(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    opp = db.query(Opportunity).filter(Opportunity.id == id).first()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    saved = db.query(SavedItem).filter(
        SavedItem.user_id == current_user.id,
        SavedItem.item_type == "opportunity",
        SavedItem.item_id == opp.id
    ).first()

    if saved:
        db.delete(saved)
        db.commit()
        return {"saved": False, "message": "Removed from saved opportunities"}
    else:
        new_saved = SavedItem(
            user_id=current_user.id,
            item_type="opportunity",
            item_id=opp.id
        )
        db.add(new_saved)
        db.commit()
        return {"saved": True, "message": "Saved to your bookmarks"}
