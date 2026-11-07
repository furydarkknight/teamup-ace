"""
Advanced TeamUp Features API Routes (Phase 8)
17 Unique TeamUp Features:
- Skill-gap heatmap per team
- "What if I join?" simulator
- Role-slot matching
- Team balance score
- Availability overlap matrix
- Team health check
- Trial sprint (24-hr mini task)
- Backup bench (ranked shortlist)
- Team Kanban task management
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.database import get_db
from app.auth import get_current_user, get_current_user_optional
from app.models import User, Team, TeamMember
from app.models_expansion import TrialSprint, BackupBench, TeamTask
from matching import get_matcher

router = APIRouter(prefix="/api/teams", tags=["Advanced TeamUp Features"])


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    assigned_to_user_id: Optional[int] = None
    priority: Optional[str] = "medium" # low, medium, high
    due_date: Optional[str] = "Tomorrow"


class TaskStatusUpdate(BaseModel):
    status: str # todo, in_progress, done


class TrialSprintStartRequest(BaseModel):
    user_id: int
    prompt: Optional[str] = "Design and build a mock architecture schema for the hackathon MVP within 24 hours."


class BackupBenchAddRequest(BaseModel):
    user_id: int
    note: Optional[str] = "Backup candidate for core builder role"


# --- 1. "WHAT IF I JOIN?" SIMULATOR ---
@router.get("/{id}/what-if")
def simulate_joining_team(
    id: int,
    candidate_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    UNIQUE FEATURE: Shows team coverage, missing skills, and match score BEFORE and AFTER a user joins.
    """
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    target_user = None
    if candidate_id:
        target_user = db.query(User).filter(User.id == candidate_id).first()
    elif current_user:
        target_user = current_user

    if not target_user:
        raise HTTPException(status_code=400, detail="Target user or authentication required for simulation")

    required_skills = team.required_skills or []
    skill_reqs = team.skill_requirements or {} # skill -> min_level
    current_team_skills = dict(team.current_skills or {}) # skill -> current_level

    # BEFORE join
    before_covered = []
    before_missing = []
    for s, min_lvl in skill_reqs.items():
        if current_team_skills.get(s, 0) >= min_lvl:
            before_covered.append(s)
        else:
            before_missing.append(s)

    before_coverage_pct = round((len(before_covered) / max(1, len(skill_reqs))) * 100, 1)

    # AFTER join
    user_profs = target_user.skill_proficiency or {}
    after_team_skills = dict(current_team_skills)
    skills_filled_by_user = []

    for s, lvl in user_profs.items():
        after_team_skills[s] = max(after_team_skills.get(s, 0), lvl)

    after_covered = []
    after_missing = []
    for s, min_lvl in skill_reqs.items():
        if after_team_skills.get(s, 0) >= min_lvl:
            after_covered.append(s)
            if s in before_missing:
                skills_filled_by_user.append(s)
        else:
            after_missing.append(s)

    after_coverage_pct = round((len(after_covered) / max(1, len(skill_reqs))) * 100, 1)

    # Calculate match score using rule-based matcher
    matcher = get_matcher()
    match_res = matcher.match_student_to_teams(target_user, [team])
    team_match_score = match_res[0].score if match_res else 65

    return {
        "team_id": team.id,
        "team_name": team.name,
        "candidate_name": target_user.name,
        "before": {
            "coverage_percent": before_coverage_pct,
            "covered_skills": before_covered,
            "missing_skills": before_missing,
            "team_size": team.current_team_size,
            "vacancies": team.vacancies
        },
        "after": {
            "coverage_percent": after_coverage_pct,
            "covered_skills": after_covered,
            "missing_skills": after_missing,
            "skills_filled_by_you": skills_filled_by_user,
            "team_size": team.current_team_size + 1,
            "vacancies": max(0, team.vacancies - 1)
        },
        "coverage_boost": round(after_coverage_pct - before_coverage_pct, 1),
        "overall_fit_score": team_match_score,
        "verdict": (
            f"⚡ Massive Synergy! Joining boosts team capability by +{round(after_coverage_pct - before_coverage_pct, 1)}% and covers critical gaps: {', '.join(skills_filled_by_user)}."
            if skills_filled_by_user else "Good alignment with team goals and preferred roles."
        )
    }


# --- 2. SKILL-GAP HEATMAP ---
@router.get("/{id}/skill-heatmap")
def get_team_skill_heatmap(id: int, db: Session = Depends(get_db)):
    """
    UNIQUE FEATURE: Returns current level vs required level for every skill, marking missing skills in red.
    """
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    skill_reqs = team.skill_requirements or {}
    current_skills = team.current_skills or {}

    heatmap = []
    for skill, min_lvl in skill_reqs.items():
        curr = current_skills.get(skill, 0)
        gap = min_lvl - curr
        heatmap.append({
            "skill": skill,
            "required_level": min_lvl,
            "current_level": curr,
            "gap": max(0, gap),
            "status": "met" if curr >= min_lvl else ("partial" if curr > 0 else "missing"),
            "color": "emerald" if curr >= min_lvl else ("amber" if curr > 0 else "rose")
        })

    return {
        "team_name": team.name,
        "heatmap": heatmap,
        "total_skills": len(skill_reqs),
        "covered_count": sum(1 for h in heatmap if h["status"] == "met"),
        "missing_count": sum(1 for h in heatmap if h["status"] == "missing")
    }


# --- 3. TEAM BALANCE SCORE & HEALTH CHECK ---
@router.get("/{id}/balance-score")
def get_team_balance_score(id: int, db: Session = Depends(get_db)):
    """
    UNIQUE FEATURE: Warns when a team is skewed (e.g. 100% backend, 0% design),
    and analyzes schedule overlap and working style health.
    """
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = [m.user for m in team.members if m.user]
    if not members:
        return {"balance_score": 50, "warnings": ["No members enrolled yet."], "recommendations": []}

    # Analyze role distribution
    roles = []
    availabilities = []
    collab_styles = []
    for u in members:
        roles.extend(u.preferred_roles or [])
        availabilities.append(u.availability)
        if u.collaboration_preference:
            collab_styles.append(u.collaboration_preference)

    has_frontend = any("Frontend" in r or "Full Stack" in r or "React" in r for r in roles)
    has_backend = any("Backend" in r or "FastAPI" in r or "Python" in r or "Full Stack" in r for r in roles)
    has_design = any("Design" in r or "UI/UX" in r for r in roles)
    has_pitch = any("Presenter" in r or "Pitching" in r or "Product" in r for r in roles)

    score = 100
    warnings = []
    recommendations = []

    if not has_frontend:
        score -= 25
        warnings.append("⚠️ Missing Frontend coverage. Your team has no dedicated UI builder.")
        recommendations.append("Recruit a Frontend Developer or UI/UX Designer.")

    if not has_backend:
        score -= 25
        warnings.append("⚠️ Missing Backend architecture. APIs and database logic need an owner.")
        recommendations.append("Recruit a Backend Developer (Python / Node / Go).")

    if not has_design:
        score -= 15
        warnings.append("⚠️ Missing UI/UX Designer. Prototypes and slide visuals may lack polish.")

    if not has_pitch:
        score -= 10
        warnings.append("⚠️ Missing Presentation lead for the final 3-minute hackathon pitch.")

    # Schedule overlap
    common_avail = len(set(availabilities)) <= 2

    return {
        "team_name": team.name,
        "balance_score": max(20, score),
        "health_status": "Balanced & Ready" if score >= 80 else ("Viable with Gaps" if score >= 50 else "Critically Skewed"),
        "warnings": warnings,
        "recommendations": recommendations,
        "coverage": {
            "frontend": has_frontend,
            "backend": has_backend,
            "design": has_design,
            "presentation": has_pitch
        },
        "schedule_synergy": "High Overlap (Smooth collaboration)" if common_avail else "Diverse availability (Coordination needed)",
        "members_count": len(members)
    }


# --- 4. KANBAN TEAM TASKS ---
@router.get("/{id}/tasks")
def list_team_tasks(id: int, db: Session = Depends(get_db)):
    tasks = db.query(TeamTask).filter(TeamTask.team_id == id).all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "assigned_to": t.assigned_to.name if t.assigned_to else "Unassigned",
            "assigned_to_avatar": t.assigned_to.avatar_url if t.assigned_to else "",
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date
        }
        for t in tasks
    ]


@router.post("/{id}/tasks")
def create_team_task(
    id: int,
    req: TaskCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    task = TeamTask(
        team_id=team.id,
        title=req.title,
        description=req.description or "",
        assigned_to_user_id=req.assigned_to_user_id or current_user.id,
        priority=req.priority or "medium",
        due_date=req.due_date or "Tomorrow",
        status="todo"
    )
    db.add(task)
    db.commit()

    return {"message": "Task added to Kanban board!", "id": task.id}


@router.put("/tasks/{task_id}")
def update_task_status(
    task_id: int,
    req: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(TeamTask).filter(TeamTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = req.status
    db.commit()
    return {"message": f"Task moved to {req.status}!", "status": req.status}


# --- 5. TRIAL SPRINT (24-HR MINI TASK) ---
@router.get("/{id}/trial-sprint")
def get_trial_sprint(id: int, db: Session = Depends(get_db)):
    sprint = db.query(TrialSprint).filter(TrialSprint.team_id == id).first()
    if not sprint:
        return {"active": False, "sprint": None}

    return {
        "active": sprint.status == "Active",
        "sprint": {
            "id": sprint.id,
            "user_name": sprint.user.name if sprint.user else "Candidate",
            "prompt": sprint.prompt,
            "start_time": sprint.start_time.strftime("%b %d, %I:%M %p") if sprint.start_time else "",
            "duration_hours": sprint.duration_hours,
            "status": sprint.status
        }
    }


@router.post("/{id}/trial-sprint")
def start_trial_sprint(
    id: int,
    req: TrialSprintStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    sprint = TrialSprint(
        team_id=team.id,
        user_id=req.user_id,
        prompt=req.prompt or "Implement a mock schema for the hackathon MVP within 24 hours.",
        status="Active"
    )
    db.add(sprint)
    db.commit()

    return {"message": "24-Hour Trial Sprint started! Both parties can evaluate fit without locking in.", "id": sprint.id}


# --- 6. BACKUP BENCH ---
@router.get("/{id}/backup-bench")
def get_backup_bench(id: int, db: Session = Depends(get_db)):
    bench = db.query(BackupBench).filter(BackupBench.team_id == id).order_by(BackupBench.rank_order).all()
    return [
        {
            "id": b.id,
            "user_id": b.user_id,
            "candidate_name": b.user.name if b.user else "Candidate",
            "candidate_avatar": b.user.avatar_url if b.user else "",
            "skills": b.user.skills if b.user else [],
            "rank_order": b.rank_order,
            "note": b.note
        }
        for b in bench
    ]


@router.post("/{id}/backup-bench")
def add_to_backup_bench(
    id: int,
    req: BackupBenchAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    team = db.query(Team).filter(Team.id == id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    count = db.query(BackupBench).filter(BackupBench.team_id == team.id).count()
    bench = BackupBench(
        team_id=team.id,
        user_id=req.user_id,
        rank_order=count + 1,
        note=req.note or "Backup candidate"
    )
    db.add(bench)
    db.commit()

    return {"message": "Candidate added to backup bench! One tap invites them if someone drops out.", "id": bench.id}
