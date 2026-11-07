"""
Organizer, Recruiter & Admin Portals API Routes (Phase 7)
Role-based dashboards, applicant review pipeline, talent search over 1,050 students,
and administrative moderation.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
import json
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Team, Event, Feedback
from app.models_expansion import (
    Opportunity, JobPosting, Application, Certificate, VerifiedSkill, Company
)

router = APIRouter(prefix="/api/portals", tags=["Role Portals (Organizer, Recruiter, Admin)"])


class OpportunityCreateRequest(BaseModel):
    title: str
    type: str = "Hackathon"
    description: str
    skills: List[str]
    location_mode: str = "Online"
    deadline: str = "In 14 days"
    prize_pool: str = "₹1,00,000"
    team_size_min: int = 1
    team_size_max: int = 4


class ApplicationStatusUpdate(BaseModel):
    status: str # Applied, Shortlisted, Interview, Selected, Rejected
    note: Optional[str] = ""
    interview_date: Optional[str] = None
    interview_link: Optional[str] = None


# ==========================================
# ORGANIZER PORTAL
# ==========================================
@router.get("/organizer/dashboard")
def get_organizer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["organizer", "admin"]:
        raise HTTPException(status_code=403, detail="Organizer portal is restricted to organizer or admin accounts.")

    my_opps = db.query(Opportunity).filter(
        or_(Opportunity.organizer_id == current_user.id, Opportunity.organizer_name.ilike(f"%{current_user.name}%"))
    ).all()

    # If organizer has no assigned opps, show first 5 for demo purposes
    if not my_opps:
        my_opps = db.query(Opportunity).limit(5).all()

    total_registrations = 0
    opp_stats = []
    for o in my_opps:
        regs = db.query(Application).filter(Application.opportunity_id == o.id).count()
        total_registrations += regs
        # Teams formed vs incomplete for event
        teams_count = db.query(Team).filter(Team.event_id == o.event_id).count() if o.event_id else 0
        opp_stats.append({
            "id": o.id,
            "title": o.title,
            "type": o.type,
            "status": o.status,
            "deadline": o.deadline,
            "registrations_count": regs,
            "teams_formed": teams_count,
            "views_count": o.views_count
        })

    return {
        "organizer_name": current_user.name,
        "college": current_user.college,
        "total_opportunities": len(my_opps),
        "total_registrations": total_registrations,
        "active_hackathons": sum(1 for o in my_opps if o.type == "Hackathon"),
        "opportunities": opp_stats
    }


@router.post("/organizer/opportunities")
def create_opportunity(
    req: OpportunityCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["organizer", "admin"]:
        raise HTTPException(status_code=403, detail="Only verified organizers can publish opportunities.")

    opp = Opportunity(
        title=req.title,
        slug=req.title.lower().replace(" ", "-")[:80],
        organizer_name=current_user.name,
        organizer_id=current_user.id,
        type=req.type,
        description=req.description,
        skills_json=json.dumps(req.skills),
        location_mode=req.location_mode,
        deadline=req.deadline,
        prize_pool=req.prize_pool,
        team_size_min=req.team_size_min,
        team_size_max=req.team_size_max,
        status="Active",
        is_featured=True
    )
    db.add(opp)
    db.commit()
    db.refresh(opp)

    return {"message": f"Opportunity '{opp.title}' published successfully!", "id": opp.id}


@router.get("/organizer/opportunities/{id}/applicants")
def list_opportunity_applicants(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    apps = db.query(Application).filter(Application.opportunity_id == id).all()
    return [
        {
            "id": a.id,
            "student_id": a.user.student_id if a.user else "",
            "student_name": a.user.name if a.user else "Applicant",
            "student_college": a.user.college if a.user else "",
            "skills": a.user.skills if a.user else [],
            "status": a.status,
            "cover_note": a.cover_note,
            "applied_at": a.created_at.strftime("%b %d, %Y") if a.created_at else ""
        }
        for a in apps
    ]


# ==========================================
# RECRUITER PORTAL & TALENT SEARCH
# ==========================================
@router.get("/recruiter/dashboard")
def get_recruiter_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["recruiter", "admin"]:
        raise HTTPException(status_code=403, detail="Recruiter portal is restricted to recruiter accounts.")

    my_jobs = db.query(JobPosting).all()[:6] # Display active postings
    total_applicants = db.query(Application).filter(Application.application_type == "job").count()

    return {
        "recruiter_name": current_user.name,
        "company_name": current_user.company_name or "Partner Enterprise",
        "active_openings": len(my_jobs),
        "total_applicants": total_applicants,
        "jobs": [
            {
                "id": j.id,
                "title": j.title,
                "job_type": j.job_type,
                "work_mode": j.work_mode,
                "stipend_salary": j.stipend_salary,
                "applicants_count": len(j.applications),
                "deadline": j.deadline
            }
            for j in my_jobs
        ]
    }


@router.get("/recruiter/talent-search")
def recruiter_talent_search(
    skill: Optional[str] = None,
    college: Optional[str] = None,
    verified_only: bool = False,
    has_certificate: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recruiter Talent Search over 1,050 student dataset:
    Filter by verified skills, college, experience, reliability score, and certificates.
    """
    query = db.query(User).filter(User.role == "student")

    if college and college != "All":
        query = query.filter(User.college.ilike(f"%{college}%"))

    if skill and skill != "All":
        query = query.filter(User.skills_json.ilike(f"%{skill}%"))

    if verified_only:
        query = query.filter(User.is_verified == True)

    total = query.count()
    users = query.order_by(desc(User.reliability_score)).offset((page - 1) * limit).limit(limit).all()

    items = []
    for u in users:
        # Check verified skills
        vs = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == u.id).all()
        vs_names = [v.skill_name for v in vs]
        certs_count = db.query(Certificate).filter(Certificate.user_id == u.id).count()

        if has_certificate and certs_count == 0:
            continue

        items.append({
            "id": u.id,
            "student_id": u.student_id or f"S{u.id:04d}",
            "name": u.name,
            "college": u.college,
            "year": u.year,
            "headline": u.headline or f"{u.experience_level} Engineer",
            "skills": u.skills,
            "verified_skills": vs_names,
            "reliability_score": round(u.reliability_score, 1),
            "certificates_count": certs_count,
            "avatar_url": u.avatar_url,
            "github_url": u.github_url,
            "portfolio_url": f"/u/{u.username or u.student_id or u.id}"
        })

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "students": items
    }


@router.put("/recruiter/applications/{app_id}/status")
def update_application_status(
    app_id: int,
    req: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app_record = db.query(Application).filter(Application.id == app_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    app_record.status = req.status
    if req.interview_date:
        try:
            app_record.interview_date = datetime.strptime(req.interview_date, "%Y-%m-%d %H:%M")
        except Exception:
            pass
    if req.interview_link:
        app_record.interview_link = req.interview_link

    # Append to timeline
    tl = app_record.status_timeline
    tl.append({
        "status": req.status,
        "timestamp": "Just now",
        "note": req.note or f"Status updated to {req.status} by recruiter"
    })
    app_record.status_timeline_json = json.dumps(tl)
    db.commit()

    return {"message": f"Candidate status updated to {req.status}!", "status": req.status}


# ==========================================
# ADMIN PORTAL
# ==========================================
@router.get("/admin/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Platform admin privileges required.")

    total_users = db.query(User).count()
    students_count = db.query(User).filter(User.role == "student").count()
    organizers_count = db.query(User).filter(User.role == "organizer").count()
    recruiters_count = db.query(User).filter(User.role == "recruiter").count()
    mentors_count = db.query(User).filter(User.is_mentor == True).count()

    total_opps = db.query(Opportunity).count()
    total_jobs = db.query(JobPosting).count()
    total_apps = db.query(Application).count()
    total_teams = db.query(Team).count()

    return {
        "metrics": {
            "total_users": total_users,
            "students": students_count,
            "organizers": organizers_count,
            "recruiters": recruiters_count,
            "mentors": mentors_count,
            "opportunities": total_opps,
            "jobs": total_jobs,
            "applications": total_apps,
            "teams": total_teams
        },
        "recent_verification_requests": [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "college": u.college,
                "is_verified": u.is_verified
            }
            for u in db.query(User).filter(User.is_verified == False).limit(5).all()
        ]
    }
