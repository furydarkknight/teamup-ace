"""
Resume Builder API Routes (Phase 2)
Auto-fills from profile, 3 templates (modern, minimal, technical), multiple resumes, default selection.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.models_expansion import Resume

router = APIRouter(prefix="/api/resumes", tags=["Resume Builder"])


class ResumeCreateRequest(BaseModel):
    title: Optional[str] = "My Resume"
    template_name: Optional[str] = "modern" # modern, minimal, technical
    data: Optional[Dict[str, Any]] = None


class ResumeUpdateRequest(BaseModel):
    title: Optional[str] = None
    template_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


@router.get("")
def list_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resumes = db.query(Resume).filter(Resume.user_id == current_user.id).all()
    if not resumes:
        # Auto-create initial resume from profile
        default_data = {
            "summary": current_user.short_bio or current_user.bio or f"Computer Science student at {current_user.college} with strong problem-solving skills.",
            "education": [
                {
                    "degree": f"Undergraduate Degree ({current_user.year})",
                    "institution": current_user.college,
                    "year": "2023 - Present",
                    "score": "8.8 CGPA"
                }
            ],
            "experience": [
                {"role": exp, "company": "Project Experience", "duration": "Recent", "details": exp}
                for exp in (current_user.project_experience or ["Built full-stack collaborative application"])
            ],
            "projects": [
                {"name": "TeamUp by ACE", "tech": "FastAPI, Tailwind, Sentence-Transformers", "description": "AI-powered teammate matching platform for international hackathons."},
                {"name": "Hackathon MVP", "tech": "Python, React, SQLite", "description": "Engineered real-time collaboration tools and scoring pipelines."}
            ],
            "skills": current_user.skills or ["Python", "JavaScript", "FastAPI"],
            "certifications": ["Verified Student Credential"]
        }
        res = Resume(
            user_id=current_user.id,
            title="Primary Resume (Auto-generated)",
            template_name="modern",
            data_json=json.dumps(default_data),
            is_default=True
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        resumes = [res]

    return [
        {
            "id": r.id,
            "title": r.title,
            "template_name": r.template_name,
            "is_default": r.is_default,
            "data": r.data,
            "updated_at": r.updated_at.strftime("%b %d, %Y") if r.updated_at else ""
        }
        for r in resumes
    ]


@router.get("/{id}")
def get_resume(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resume not found")

    return {
        "id": res.id,
        "title": res.title,
        "template_name": res.template_name,
        "is_default": res.is_default,
        "data": res.data,
        "user_name": current_user.name,
        "user_email": current_user.email,
        "user_college": current_user.college,
        "github_url": current_user.github_url,
        "linkedin_url": current_user.linkedin_url
    }


@router.post("")
def create_resume(
    req: ResumeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = req.data
    if not data:
        data = {
            "summary": current_user.bio or current_user.short_bio or f"Engineering student at {current_user.college}.",
            "education": [{"degree": "Undergraduate", "institution": current_user.college, "year": "2023 - Present"}],
            "experience": [],
            "projects": [],
            "skills": current_user.skills,
            "certifications": []
        }

    res = Resume(
        user_id=current_user.id,
        title=req.title or "My Resume",
        template_name=req.template_name or "modern",
        data_json=json.dumps(data),
        is_default=False
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    return {"message": "Resume created successfully!", "id": res.id}


@router.put("/{id}")
def update_resume(
    id: int,
    req: ResumeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resume not found")

    if req.title is not None:
        res.title = req.title
    if req.template_name is not None:
        res.template_name = req.template_name
    if req.data is not None:
        res.data = req.data
    if req.is_default:
        db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_default": False})
        res.is_default = True

    db.commit()
    return {"message": "Resume updated successfully!"}


@router.delete("/{id}")
def delete_resume(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resume not found")

    db.delete(res)
    db.commit()
    return {"message": "Resume deleted successfully"}


@router.post("/{id}/set-default")
def set_default_resume(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(Resume).filter(Resume.id == id, Resume.user_id == current_user.id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resume not found")

    db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_default": False})
    res.is_default = True
    db.commit()
    return {"message": f"'{res.title}' set as your default resume."}
