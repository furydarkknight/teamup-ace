"""
Community & Career Support API Routes (Phase 6)
Mentorship directory & booking, verified alumni referral requests, discussion forums,
college campus clubs, and hackathon project submissions with judging.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from datetime import datetime
import json

from app.database import get_db
from app.auth import get_current_user_optional, get_current_user
from app.models import User, Team
from app.models_expansion import (
    MentorProfile, MentorshipSession, AlumniProfile, ReferralRequest,
    ForumThread, ForumPost, College, Club, ProjectSubmission, JudgingScore, Opportunity
)

router = APIRouter(prefix="/api/community", tags=["Community & Career Support"])


class MentorshipBookingRequest(BaseModel):
    mentor_id: int
    scheduled_at: str
    topic: str
    opportunity_id: Optional[int] = None


class ReferralApplyRequest(BaseModel):
    alumni_id: int
    job_url: str
    resume_link: str
    note: str


class ForumThreadCreate(BaseModel):
    title: str
    content: str
    opportunity_id: Optional[int] = None
    skill_name: Optional[str] = None


class ForumPostCreate(BaseModel):
    content: str


class ProjectSubmissionCreate(BaseModel):
    team_id: int
    opportunity_id: Optional[int] = None
    title: str
    tagline: Optional[str] = ""
    description: str
    repo_url: str
    demo_url: Optional[str] = ""


# --- MENTORSHIP ---
@router.get("/mentors")
def list_mentors(
    skill: Optional[str] = None,
    company: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(MentorProfile).filter(MentorProfile.is_approved == True)
    if company:
        query = query.filter(MentorProfile.company.ilike(f"%{company}%"))
    if skill:
        query = query.filter(MentorProfile.expertise_skills_json.ilike(f"%{skill}%"))

    mentors = query.all()
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "name": m.user.name if m.user else "Mentor",
            "avatar_url": m.user.avatar_url if m.user else "",
            "company": m.company,
            "job_title": m.job_title,
            "expertise_skills": m.expertise_skills,
            "years_experience": m.years_experience,
            "bio": m.bio,
            "rating": m.rating,
            "sessions_count": m.sessions_count,
            "available_slots": m.available_slots
        }
        for m in mentors
    ]


@router.post("/mentors/book")
def book_mentor_session(
    req: MentorshipBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mentor_prof = db.query(MentorProfile).filter((MentorProfile.user_id == req.mentor_id) | (MentorProfile.id == req.mentor_id)).first()
    if not mentor_prof:
        raise HTTPException(status_code=404, detail="Mentor not found")

    session = MentorshipSession(
        mentor_id=req.mentor_id,
        mentee_id=current_user.id,
        opportunity_id=req.opportunity_id,
        scheduled_at=req.scheduled_at,
        topic=req.topic,
        status="Scheduled"
    )
    db.add(session)
    db.commit()

    return {
        "message": f"Session booked with {mentor_prof.user.name if mentor_prof.user else 'Mentor'}!",
        "session_id": session.id,
        "scheduled_at": req.scheduled_at
    }


# --- ALUMNI & REFERRALS ---
@router.get("/alumni")
def list_alumni(
    college: Optional[str] = None,
    company: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AlumniProfile)
    if college and college != "All":
        query = query.filter(AlumniProfile.college.ilike(f"%{college}%"))
    if company and company != "All":
        query = query.filter(AlumniProfile.company.ilike(f"%{company}%"))

    alumni_list = query.all()
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "name": a.user.name if a.user else "Alumni",
            "college": a.college,
            "graduation_year": a.graduation_year,
            "company": a.company,
            "current_role": a.current_role,
            "can_refer": a.can_refer,
            "linkedin_url": a.linkedin_url
        }
        for a in alumni_list
    ]


@router.post("/alumni/referral-request")
def request_referral(
    req: ReferralApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alumni = db.query(AlumniProfile).filter((AlumniProfile.user_id == req.alumni_id) | (AlumniProfile.id == req.alumni_id)).first()
    if not alumni:
        raise HTTPException(status_code=404, detail="Alumni profile not found")

    ref = ReferralRequest(
        student_id=current_user.id,
        alumni_id=req.alumni_id,
        job_url=req.job_url,
        resume_link=req.resume_link,
        note=req.note,
        status="Pending"
    )
    db.add(ref)
    db.commit()

    return {"message": f"Referral request delivered to {alumni.user.name if alumni.user else 'Alumni'} at {alumni.company}!", "id": ref.id}


# --- DISCUSSION FORUMS ---
@router.get("/forum/threads")
def list_forum_threads(
    opportunity_id: Optional[int] = None,
    skill: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ForumThread)
    if opportunity_id:
        query = query.filter(ForumThread.opportunity_id == opportunity_id)
    if skill:
        query = query.filter(ForumThread.skill_name == skill)

    threads = query.order_by(desc(ForumThread.is_pinned), desc(ForumThread.created_at)).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "content": t.content,
            "author_name": t.user.name if t.user else "Student",
            "author_college": t.user.college if t.user else "",
            "upvotes_count": t.upvotes_count,
            "replies_count": len(t.posts),
            "is_pinned": t.is_pinned,
            "created_at": t.created_at.strftime("%b %d") if t.created_at else ""
        }
        for t in threads
    ]


@router.post("/forum/threads")
def create_forum_thread(
    req: ForumThreadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    thread = ForumThread(
        user_id=current_user.id,
        opportunity_id=req.opportunity_id,
        skill_name=req.skill_name,
        title=req.title,
        content=req.content
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return {"message": "Thread created successfully!", "id": thread.id}


@router.post("/forum/threads/{id}/posts")
def reply_to_forum_thread(
    id: int,
    req: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    thread = db.query(ForumThread).filter(ForumThread.id == id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    post = ForumPost(
        thread_id=thread.id,
        user_id=current_user.id,
        content=req.content
    )
    db.add(post)
    thread.replies_count = (thread.replies_count or 0) + 1
    db.commit()

    return {"message": "Reply posted!", "id": post.id}


# --- COLLEGES & CLUBS ---
@router.get("/colleges")
def list_colleges_with_clubs(db: Session = Depends(get_db)):
    colleges = db.query(College).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "city": c.city,
            "state": c.state,
            "domain": c.domain,
            "description": c.description,
            "student_count": c.student_count,
            "logo_url": c.logo_url,
            "clubs": [
                {
                    "id": cl.id,
                    "name": cl.name,
                    "category": cl.category,
                    "description": cl.description,
                    "members_count": cl.members_count
                }
                for cl in c.clubs
            ]
        }
        for c in colleges
    ]


# --- PROJECT SUBMISSIONS ---
@router.post("/submissions")
def submit_project(
    req: ProjectSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == req.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    sub = ProjectSubmission(
        team_id=req.team_id,
        opportunity_id=req.opportunity_id or (team.event_id if team else None),
        title=req.title,
        tagline=req.tagline or "",
        description=req.description,
        repo_url=req.repo_url,
        demo_url=req.demo_url or ""
    )
    db.add(sub)
    db.commit()

    return {"message": f"Project '{sub.title}' submitted for judging!", "id": sub.id}


@router.get("/submissions/opportunity/{opp_id}")
def list_submissions_for_opportunity(opp_id: int, db: Session = Depends(get_db)):
    subs = db.query(ProjectSubmission).filter(ProjectSubmission.opportunity_id == opp_id).all()
    return [
        {
            "id": s.id,
            "team_id": s.team_id,
            "team_name": s.team.name if s.team else "Team",
            "title": s.title,
            "tagline": s.tagline,
            "description": s.description,
            "repo_url": s.repo_url,
            "demo_url": s.demo_url,
            "submitted_at": s.submitted_at.strftime("%b %d, %Y") if s.submitted_at else ""
        }
        for s in subs
    ]
