"""
Unified Global Search API (Global Rule)
Search query across Opportunities, Jobs, Courses, Teams, Students, Colleges, and Mentors.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database import get_db
from app.models import User, Team, Event
from app.models_expansion import Opportunity, JobPosting, Course, College, MentorProfile

router = APIRouter(prefix="/api/search", tags=["Global Search"])


@router.get("")
def global_search(
    q: str = Query(..., min_length=1, description="Global search query"),
    db: Session = Depends(get_db)
):
    query_str = f"%{q.lower()}%"

    # 1. Opportunities
    opps = db.query(Opportunity).filter(
        or_(
            Opportunity.title.ilike(query_str),
            Opportunity.organizer_name.ilike(query_str),
            Opportunity.skills_json.ilike(query_str),
            Opportunity.type.ilike(query_str)
        )
    ).limit(5).all()

    # 2. Jobs
    jobs = db.query(JobPosting).filter(
        or_(
            JobPosting.title.ilike(query_str),
            JobPosting.skills_required_json.ilike(query_str),
            JobPosting.role_category.ilike(query_str)
        )
    ).limit(5).all()

    # 3. Courses
    courses = db.query(Course).filter(
        or_(
            Course.title.ilike(query_str),
            Course.skill_tags_json.ilike(query_str)
        )
    ).limit(5).all()

    # 4. Teams
    teams = db.query(Team).filter(
        or_(
            Team.name.ilike(query_str),
            Team.required_skills_json.ilike(query_str),
            Team.college.ilike(query_str)
        )
    ).limit(5).all()

    # 5. Students / People
    students = db.query(User).filter(
        or_(
            User.name.ilike(query_str),
            User.skills_json.ilike(query_str),
            User.college.ilike(query_str)
        )
    ).limit(5).all()

    return {
        "query": q,
        "results": {
            "opportunities": [
                {
                    "id": o.id,
                    "title": o.title,
                    "type": o.type,
                    "organizer": o.organizer_name,
                    "deadline": o.deadline,
                    "url": f"#opp-{o.id}"
                }
                for o in opps
            ],
            "jobs": [
                {
                    "id": j.id,
                    "title": j.title,
                    "company": j.company.name if j.company else "Company",
                    "stipend": j.stipend_salary,
                    "url": f"#job-{j.id}"
                }
                for j in jobs
            ],
            "courses": [
                {
                    "id": c.id,
                    "title": c.title,
                    "level": c.level,
                    "duration": c.duration,
                    "url": f"#course-{c.id}"
                }
                for c in courses
            ],
            "teams": [
                {
                    "id": t.id,
                    "name": t.name,
                    "college": t.college,
                    "vacancies": t.vacancies,
                    "url": f"#team-{t.id}"
                }
                for t in teams
            ],
            "people": [
                {
                    "id": u.id,
                    "name": u.name,
                    "college": u.college,
                    "skills": u.skills[:3],
                    "url": f"#portfolio-{u.username or u.student_id or u.id}"
                }
                for u in students
            ]
        }
    }
