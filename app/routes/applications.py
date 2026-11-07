"""
Applications & Tracking API Routes (Phase 3)
My Space tabs: Applied, Saved, Registered, Shortlisted, Rejected, Selected, Withdrawn.
Timeline history, withdrawal, upcoming deadlines, and bookmarking.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.models_expansion import Application, Opportunity, JobPosting, SavedItem, Certificate

router = APIRouter(prefix="/api/applications", tags=["My Space & Applications"])


@router.get("/my")
def get_my_applications(
    status_tab: Optional[str] = Query("all", description="all, applied, registered, shortlisted, interview, selected, rejected, withdrawn"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).filter(Application.user_id == current_user.id)

    if status_tab and status_tab != "all":
        query = query.filter(Application.status.ilike(status_tab))

    apps = query.order_by(desc(Application.updated_at)).all()

    items = []
    for a in apps:
        item = {
            "id": a.id,
            "application_type": a.application_type,
            "status": a.status,
            "timeline": a.status_timeline,
            "cover_note": a.cover_note,
            "expected_stipend": a.expected_stipend,
            "interview_date": a.interview_date.strftime("%b %d, %Y - %I:%M %p") if a.interview_date else None,
            "interview_link": a.interview_link,
            "created_at": a.created_at.strftime("%b %d, %Y") if a.created_at else "",
            "opportunity": None,
            "job": None
        }

        if a.opportunity:
            item["opportunity"] = {
                "id": a.opportunity.id,
                "title": a.opportunity.title,
                "organizer_name": a.opportunity.organizer_name,
                "type": a.opportunity.type,
                "deadline": a.opportunity.deadline,
                "prize_pool": a.opportunity.prize_pool,
                "banner_url": a.opportunity.banner_url
            }

        if a.job_posting:
            item["job"] = {
                "id": a.job_posting.id,
                "title": a.job_posting.title,
                "company_name": a.job_posting.company.name if a.job_posting.company else "Company",
                "company_logo": a.job_posting.company.logo_url if a.job_posting.company else "",
                "job_type": a.job_posting.job_type,
                "stipend_salary": a.job_posting.stipend_salary,
                "deadline": a.job_posting.deadline
            }

        items.append(item)

    # Compute summary counts
    all_my_apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    counts = {
        "all": len(all_my_apps),
        "applied": sum(1 for x in all_my_apps if x.status.lower() == "applied"),
        "registered": sum(1 for x in all_my_apps if x.status.lower() == "registered"),
        "shortlisted": sum(1 for x in all_my_apps if x.status.lower() == "shortlisted"),
        "interview": sum(1 for x in all_my_apps if x.status.lower() == "interview"),
        "selected": sum(1 for x in all_my_apps if x.status.lower() == "selected"),
        "rejected": sum(1 for x in all_my_apps if x.status.lower() == "rejected"),
        "withdrawn": sum(1 for x in all_my_apps if x.status.lower() == "withdrawn")
    }

    # Profile completeness score
    score = 40
    if current_user.skills: score += 20
    if current_user.github_url or current_user.linkedin_url: score += 15
    if current_user.is_verified: score += 15
    cert_count = db.query(Certificate).filter(Certificate.user_id == current_user.id).count()
    if cert_count > 0: score += 10
    profile_completeness = min(100, score)

    return {
        "items": items,
        "counts": counts,
        "profile_completeness": profile_completeness
    }


@router.post("/{id}/withdraw")
def withdraw_application(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app_record = db.query(Application).filter(Application.id == id, Application.user_id == current_user.id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    app_record.status = "Withdrawn"
    tl = app_record.status_timeline
    tl.append({"status": "Withdrawn", "timestamp": "Just now", "note": "Application withdrawn by candidate"})
    app_record.status_timeline_json = json.dumps(tl)
    db.commit()

    return {"message": "Application withdrawn successfully", "status": "Withdrawn"}


@router.get("/saved")
def get_saved_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    saved = db.query(SavedItem).filter(SavedItem.user_id == current_user.id).order_by(desc(SavedItem.created_at)).all()
    results = []

    for s in saved:
        obj = {"id": s.id, "item_type": s.item_type, "item_id": s.item_id, "data": None}
        if s.item_type == "opportunity":
            opp = db.query(Opportunity).filter(Opportunity.id == s.item_id).first()
            if opp:
                obj["data"] = {
                    "title": opp.title,
                    "organizer": opp.organizer_name,
                    "type": opp.type,
                    "deadline": opp.deadline,
                    "prize": opp.prize_pool,
                    "banner": opp.banner_url
                }
        elif s.item_type == "job":
            job = db.query(JobPosting).filter(JobPosting.id == s.item_id).first()
            if job:
                obj["data"] = {
                    "title": job.title,
                    "company": job.company.name if job.company else "Company",
                    "logo": job.company.logo_url if job.company else "",
                    "stipend": job.stipend_salary,
                    "deadline": job.deadline
                }
        if obj["data"]:
            results.append(obj)

    return results


@router.post("/saved/toggle")
def toggle_save_item(
    item_type: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(SavedItem).filter(
        SavedItem.user_id == current_user.id,
        SavedItem.item_type == item_type,
        SavedItem.item_id == item_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"saved": False, "message": f"Removed from saved {item_type}s"}
    else:
        new_item = SavedItem(user_id=current_user.id, item_type=item_type, item_id=item_id)
        db.add(new_item)
        db.commit()
        return {"saved": True, "message": f"Saved {item_type} to your bookmarks"}
