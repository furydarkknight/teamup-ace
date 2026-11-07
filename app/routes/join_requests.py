from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import User, TeamJoinRequest, TeamMember, Team
from app.schemas import JoinRequestUpdateStatus, TeamJoinRequestResponse

router = APIRouter(prefix="/api/join-requests", tags=["Join Requests"])

@router.put("/{request_id}", response_model=TeamJoinRequestResponse)
def update_join_request(
    request_id: int,
    data: JoinRequestUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept or decline a join request. Only team lead can accept/decline."""
    jr = db.query(TeamJoinRequest).filter(TeamJoinRequest.id == request_id).first()
    if not jr:
        raise HTTPException(status_code=404, detail="Join request not found")

    team = db.query(Team).filter(Team.id == jr.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the team lead can accept/decline requests")

    if jr.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {jr.status}")

    if data.status not in ("accepted", "declined"):
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'declined'")

    jr.status = data.status
    
    if data.status == "accepted":
        if team.vacancies <= 0:
            raise HTTPException(status_code=400, detail="Team has no vacancies left")

        already = db.query(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == jr.user_id
        ).first()
        if not already:
            new_member = TeamMember(
                team_id=team.id,
                user_id=jr.user_id,
                role="Member"
            )
            db.add(new_member)

            members = list(team.current_members or [])
            if jr.student_id and jr.student_id not in members:
                members.append(jr.student_id)
            team.current_members = members

            student = db.query(User).filter(User.id == jr.user_id).first()
            if student:
                current_skills = dict(team.current_skills or {})
                for skill, level in (student.skill_proficiency or {}).items():
                    if skill not in current_skills or current_skills[skill] < level:
                        current_skills[skill] = level
                team.current_skills = current_skills

            team.vacancies = max(0, team.vacancies - 1)

    db.commit()
    db.refresh(jr)

    return TeamJoinRequestResponse(
        id=jr.id,
        team_id=jr.team_id,
        team_name=team.team_name or team.name,
        user_id=jr.user_id,
        student_id=jr.student_id,
        student_name=jr.user.name if jr.user else "Student",
        student_avatar=jr.user.avatar_url if jr.user else "",
        message=jr.message,
        status=jr.status,
        created_at=jr.created_at,
    )
