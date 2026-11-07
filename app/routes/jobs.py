"""
Jobs & Internships Portal API Routes (Phase 2)
Company profiles, job listings, 1-click apply, skill-based recommendations, and job alerts.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
import json

from app.database import get_db
from app.auth import get_current_user_optional, get_current_user
from app.models import User
from app.models_expansion import Company, JobPosting, Application, Resume, JobAlert, SavedItem

router = APIRouter(prefix="/api/jobs", tags=["Jobs & Internships"])


class JobApplyRequest(BaseModel):
    resume_id: Optional[int] = None
    cover_note: Optional[str] = ""
    screening_answers: Optional[dict] = {}
    expected_stipend: Optional[str] = ""


class JobAlertRequest(BaseModel):
    keyword: Optional[str] = ""
    role: Optional[str] = ""
    location: Optional[str] = ""
    min_stipend: Optional[str] = ""


@router.get("")
def list_jobs(
    role_category: Optional[str] = None,
    job_type: Optional[str] = None,
    work_mode: Optional[str] = None,
    company_id: Optional[int] = None,
    skill: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(JobPosting).filter(JobPosting.is_active == True)

    if role_category and role_category != "All":
        query = query.filter(JobPosting.role_category == role_category)

    if job_type and job_type != "All":
        query = query.filter(JobPosting.job_type == job_type)

    if work_mode and work_mode != "All":
        query = query.filter(JobPosting.work_mode == work_mode)

    if company_id:
        query = query.filter(JobPosting.company_id == company_id)

    if skill and skill != "All":
        query = query.filter(JobPosting.skills_required_json.ilike(f"%{skill}%"))

    if search:
        s = f"%{search.lower()}%"
        query = query.join(Company).filter(
            or_(
                JobPosting.title.ilike(s),
                Company.name.ilike(s),
                JobPosting.description.ilike(s),
                JobPosting.role_category.ilike(s)
            )
        )

    total = query.count()
    items = query.order_by(desc(JobPosting.created_at)).offset((page - 1) * limit).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "items": [
            {
                "id": j.id,
                "title": j.title,
                "company_id": j.company_id,
                "company_name": j.company.name if j.company else "Tech Company",
                "company_logo": j.company.logo_url if j.company else "",
                "role_category": j.role_category,
                "job_type": j.job_type,
                "work_mode": j.work_mode,
                "location": j.location,
                "duration": j.duration,
                "openings_count": j.openings_count,
                "stipend_salary": j.stipend_salary,
                "skills_required": j.skills_required,
                "experience_required": j.experience_required,
                "description": j.description,
                "deadline": j.deadline,
                "created_at": j.created_at.strftime("%b %d, %Y") if j.created_at else ""
            }
            for j in items
        ]
    }


@router.get("/recommendations")
def get_job_recommendations(
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Skill-based job matching: compares user skills & proficiencies against job required skills.
    Returns match percentage, why recommended, and missing skills.
    """
    user_skills = set(current_user.skills or [])
    user_profs = current_user.skill_proficiency or {}

    jobs = db.query(JobPosting).filter(JobPosting.is_active == True).all()
    ranked = []

    for j in jobs:
        req = set(j.skills_required or [])
        if not req:
            score = 60
            covered = []
            missing = []
        else:
            covered = list(user_skills.intersection(req))
            missing = list(req.difference(user_skills))
            # Skill coverage percentage
            base_ratio = len(covered) / len(req)
            score = int(base_ratio * 70)
            
            # Bonus for high proficiency in covered skills
            prof_bonus = sum(user_profs.get(s, 2) for s in covered) * 3
            score = min(99, max(40, score + prof_bonus))

        ranked.append({
            "job": {
                "id": j.id,
                "title": j.title,
                "company_name": j.company.name if j.company else "Company",
                "company_logo": j.company.logo_url if j.company else "",
                "job_type": j.job_type,
                "work_mode": j.work_mode,
                "location": j.location,
                "stipend_salary": j.stipend_salary,
                "skills_required": j.skills_required,
                "deadline": j.deadline
            },
            "match_score": score,
            "covered_skills": covered,
            "missing_skills": missing,
            "why_recommended": (
                f"Matches {len(covered)} of your skills ({', '.join(covered[:3])})."
                if covered else "Great entry point for your preferred roles."
            )
        })

    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return ranked[:limit]


@router.get("/companies")
def list_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "logo_url": c.logo_url,
            "industry": c.industry,
            "size": c.size,
            "location": c.location,
            "about": c.about,
            "culture": c.culture,
            "benefits": c.benefits,
            "verified": c.verified,
            "openings_count": db.query(JobPosting).filter(JobPosting.company_id == c.id, JobPosting.is_active == True).count()
        }
        for c in companies
    ]


@router.get("/companies/{id}")
def get_company_detail(id: int, db: Session = Depends(get_db)):
    comp = db.query(Company).filter(Company.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Company not found")

    openings = db.query(JobPosting).filter(
        JobPosting.company_id == comp.id,
        JobPosting.is_active == True
    ).all()

    return {
        "id": comp.id,
        "name": comp.name,
        "slug": comp.slug,
        "logo_url": comp.logo_url,
        "industry": comp.industry,
        "size": comp.size,
        "location": comp.location,
        "website": comp.website,
        "about": comp.about,
        "culture": comp.culture,
        "benefits": comp.benefits,
        "verified": comp.verified,
        "openings": [
            {
                "id": j.id,
                "title": j.title,
                "job_type": j.job_type,
                "work_mode": j.work_mode,
                "stipend_salary": j.stipend_salary,
                "skills_required": j.skills_required,
                "deadline": j.deadline
            }
            for j in openings
        ]
    }


@router.get("/{id}")
def get_job_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    job = db.query(JobPosting).filter(JobPosting.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    has_applied = False
    is_saved = False
    if current_user:
        app_record = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.job_posting_id == job.id
        ).first()
        has_applied = app_record is not None
        saved_record = db.query(SavedItem).filter(
            SavedItem.user_id == current_user.id,
            SavedItem.item_type == "job",
            SavedItem.item_id == job.id
        ).first()
        is_saved = saved_record is not None

    return {
        "id": job.id,
        "title": job.title,
        "company_id": job.company_id,
        "company_name": job.company.name if job.company else "Tech Company",
        "company_logo": job.company.logo_url if job.company else "",
        "company_about": job.company.about if job.company else "",
        "company_website": job.company.website if job.company else "",
        "role_category": job.role_category,
        "job_type": job.job_type,
        "work_mode": job.work_mode,
        "location": job.location,
        "duration": job.duration,
        "openings_count": job.openings_count,
        "stipend_salary": job.stipend_salary,
        "skills_required": job.skills_required,
        "experience_required": job.experience_required,
        "description": job.description,
        "perks": job.perks,
        "selection_process": job.selection_process,
        "screening_questions": job.screening_questions,
        "deadline": job.deadline,
        "has_applied": has_applied,
        "is_saved": is_saved
    }


@router.post("/{id}/apply")
def apply_to_job(
    id: int,
    req: JobApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobPosting).filter(JobPosting.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_posting_id == job.id
    ).first()
    if existing:
        return {"message": "You have already applied to this role", "status": existing.status}

    app_entry = Application(
        user_id=current_user.id,
        job_posting_id=job.id,
        application_type="job",
        status="Applied",
        resume_id=req.resume_id,
        cover_note=req.cover_note or "",
        screening_answers_json=json.dumps(req.screening_answers or {}),
        expected_stipend=req.expected_stipend or job.stipend_salary,
        status_timeline_json='[{"status": "Applied", "timestamp": "Just now", "note": "Application received and queued for review"}]'
    )
    db.add(app_entry)
    db.commit()

    return {
        "message": f"Application submitted to {job.company.name if job.company else 'Company'}!",
        "application_id": app_entry.id,
        "status": "Applied"
    }


@router.post("/alerts")
def create_job_alert(
    req: JobAlertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = JobAlert(
        user_id=current_user.id,
        keyword=req.keyword or "",
        role=req.role or "",
        location=req.location or "",
        min_stipend=req.min_stipend or ""
    )
    db.add(alert)
    db.commit()
    return {"message": "Job alert configured! You will receive notifications when matching jobs appear.", "id": alert.id}
