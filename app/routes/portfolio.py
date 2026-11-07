"""
Digital Portfolio API Routes (Phase 5)
Public profile /u/{username}, verified skills with proof attachments, peer endorsements, and achievements.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Feedback, TeamMember
from app.models_expansion import Certificate, VerifiedSkill, UserBadge, Badge

router = APIRouter(prefix="/api/portfolio", tags=["Digital Portfolio & Verified Skills"])


class VerifySkillRequest(BaseModel):
    skill_name: str
    verification_type: str = "github" # github, certificate, assessment
    proof_link: str


@router.get("/u/{identifier}")
def get_public_portfolio(identifier: str, db: Session = Depends(get_db)):
    """
    Public digital portfolio by username or student_id.
    """
    user = db.query(User).filter(
        or_(
            User.username == identifier,
            User.student_id == identifier,
            User.email == identifier
        )
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Student portfolio not found")

    # Fetch verified skills
    verified_skills_objs = db.query(VerifiedSkill).filter(VerifiedSkill.user_id == user.id).all()
    verified_skills_set = {v.skill_name: v.proof_link for v in verified_skills_objs}

    # Format skills with proficiency and verified status
    user_skills = user.skills or []
    user_profs = user.skill_proficiency or {}
    skills_data = [
        {
            "name": s,
            "level": user_profs.get(s, 3),
            "is_verified": s in verified_skills_set,
            "proof_link": verified_skills_set.get(s, "")
        }
        for s in user_skills
    ]

    # Fetch certificates
    certs = db.query(Certificate).filter(Certificate.user_id == user.id).all()
    certificates_data = [
        {
            "unique_id": c.unique_id,
            "title": c.title,
            "issuer": c.issuer,
            "type": c.certificate_type,
            "issue_date": c.issue_date.strftime("%b %Y") if c.issue_date else "",
            "verify_url": f"/verify/{c.unique_id}"
        }
        for c in certs
    ]

    # Fetch badges
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == user.id).all()
    badges_data = [
        {
            "code": ub.badge.code,
            "name": ub.badge.name,
            "description": ub.badge.description,
            "icon": ub.badge.icon,
            "awarded_at": ub.awarded_at.strftime("%b %Y") if ub.awarded_at else ""
        }
        for ub in user_badges if ub.badge
    ]

    # Peer feedback summary
    feedbacks = db.query(Feedback).filter(Feedback.to_user_id == user.id).all()
    all_tags = []
    reviews = []
    for f in feedbacks:
        all_tags.extend(f.tags or [])
        if f.comment:
            reviews.append({
                "rating": f.rating,
                "comment": f.comment,
                "created_at": f.created_at.strftime("%b %Y") if f.created_at else ""
            })

    # Top tags
    tag_counts = {}
    for t in all_tags:
        tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Hackathon team history
    memberships = db.query(TeamMember).filter(TeamMember.user_id == user.id).all()
    teams_history = [
        {
            "team_name": m.team.name if m.team else "Team",
            "role": m.role or "Member",
            "event_name": m.team.event.name if m.team and m.team.event else "Hackathon",
            "year": m.joined_at.strftime("%Y") if m.joined_at else "2026"
        }
        for m in memberships if m.team
    ]

    return {
        "user_id": user.id,
        "name": user.name,
        "username": user.username or f"user{user.id}",
        "headline": user.headline or f"{user.year} Student @ {user.college}",
        "college": user.college,
        "city": user.city,
        "year": user.year,
        "bio": user.bio or user.short_bio,
        "avatar_url": user.avatar_url,
        "is_verified": user.is_verified,
        "reliability_score": round(user.reliability_score, 1),
        "ratings_count": user.ratings_count,
        "github_url": user.github_url,
        "linkedin_url": user.linkedin_url,
        "points": user.points or 0,
        "skills": skills_data,
        "certificates": certificates_data,
        "badges": badges_data,
        "endorsement_tags": [t[0] for t in top_tags],
        "peer_reviews": reviews[:5],
        "teams_history": teams_history,
        "preferred_roles": user.preferred_roles,
        "collaboration_preference": user.collaboration_preference
    }


@router.post("/verify-skill")
def attach_skill_verification(
    req: VerifySkillRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    UNIQUE FEATURE: Attach GitHub repository, live URL, or credential proof to earn a Verified Skill badge.
    """
    if not req.proof_link.strip():
        raise HTTPException(status_code=400, detail="Proof link is required (e.g. GitHub repo, demo URL)")

    existing = db.query(VerifiedSkill).filter(
        VerifiedSkill.user_id == current_user.id,
        VerifiedSkill.skill_name == req.skill_name
    ).first()

    if existing:
        existing.proof_link = req.proof_link
        existing.verification_type = req.verification_type
    else:
        vs = VerifiedSkill(
            user_id=current_user.id,
            skill_name=req.skill_name,
            verification_type=req.verification_type,
            proof_link=req.proof_link
        )
        db.add(vs)

    db.commit()
    return {
        "message": f"Verified badge attached to skill '{req.skill_name}'!",
        "skill": req.skill_name,
        "proof_link": req.proof_link
    }
