from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Team, TeamMember, Event, User, TeamMessage
from app.auth import get_current_user, get_current_verified_user
from app.schemas import (
    TeamCreate, TeamResponse, TeamMemberResponse,
    TeamGapAnalysisResponse, TeamMessageCreate, TeamMessageResponse,
    UserPublicResponse
)
from app.gap_analyzer import analyze_team_gaps

router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.get("", response_model=List[TeamResponse])
def get_teams(
    event_id: Optional[int] = None,
    my_teams_only: Optional[bool] = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Team)

    if event_id:
        query = query.filter(Team.event_id == event_id)

    if my_teams_only:
        team_ids = [m.team_id for m in current_user.memberships]
        query = query.filter(Team.id.in_(team_ids))

    teams = query.order_by(Team.created_at.desc()).all()
    results = []

    for team in teams:
        members_res = []
        for m in team.members:
            members_res.append(TeamMemberResponse(
                id=m.id,
                user_id=m.user_id,
                user=UserPublicResponse.from_orm(m.user),
                role=m.role,
                joined_at=m.joined_at
            ))
        results.append(TeamResponse(
            id=team.id,
            event_id=team.event_id,
            event_name=team.event.name if team.event else "",
            name=team.name,
            tagline=team.tagline,
            leader_id=team.leader_id,
            pitch=team.pitch,
            members=members_res,
            created_at=team.created_at
        ))

    return results

@router.post("", response_model=TeamResponse)
def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_team = Team(
        event_id=data.event_id,
        name=data.name.strip(),
        tagline=data.tagline.strip() if data.tagline else "Innovating at ACE Hackathon",
        leader_id=current_user.id,
        pitch=data.pitch.strip() if data.pitch else ""
    )
    db.add(new_team)
    db.flush()

    # Add leader as initial member
    leader_member = TeamMember(
        team_id=new_team.id,
        user_id=current_user.id,
        role=data.leader_role.strip() if data.leader_role else "Team Lead"
    )
    db.add(leader_member)
    db.commit()
    db.refresh(new_team)

    return TeamResponse(
        id=new_team.id,
        event_id=new_team.event_id,
        event_name=event.name,
        name=new_team.name,
        tagline=new_team.tagline,
        leader_id=new_team.leader_id,
        pitch=new_team.pitch,
        members=[TeamMemberResponse(
            id=leader_member.id,
            user_id=current_user.id,
            user=UserPublicResponse.from_orm(current_user),
            role=leader_member.role,
            joined_at=leader_member.joined_at
        )],
        created_at=new_team.created_at
    )

@router.get("/{team_id}", response_model=TeamResponse)
def get_team_detail(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members_res = []
    for m in team.members:
        members_res.append(TeamMemberResponse(
            id=m.id,
            user_id=m.user_id,
            user=UserPublicResponse.from_orm(m.user),
            role=m.role,
            joined_at=m.joined_at
        ))

    return TeamResponse(
        id=team.id,
        event_id=team.event_id,
        event_name=team.event.name if team.event else "",
        name=team.name,
        tagline=team.tagline,
        leader_id=team.leader_id,
        pitch=team.pitch,
        members=members_res,
        created_at=team.created_at
    )

@router.get("/{team_id}/gaps", response_model=TeamGapAnalysisResponse)
def get_team_gap_analysis(
    team_id: int,
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    analysis = analyze_team_gaps(team, team.event, db)
    return analysis

@router.post("/{team_id}/messages", response_model=TeamMessageResponse)
def send_team_message(
    team_id: int,
    data: TeamMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Verify user is a member of this team
    is_member = any(m.user_id == current_user.id for m in team.members)
    if not is_member and team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="You must be a member of this team to chat")

    msg = TeamMessage(
        team_id=team_id,
        sender_id=current_user.id,
        content=data.content.strip()
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return TeamMessageResponse(
        id=msg.id,
        team_id=msg.team_id,
        sender_id=msg.sender_id,
        sender_name=current_user.name,
        sender_avatar=current_user.avatar_url,
        content=msg.content,
        created_at=msg.created_at
    )

@router.get("/{team_id}/messages", response_model=List[TeamMessageResponse])
def get_team_messages(
    team_id: int,
    limit: Optional[int] = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Member check
    is_member = any(m.user_id == current_user.id for m in team.members)
    if not is_member and team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="You must be a member of this team to view chat")

    messages = db.query(TeamMessage).filter(TeamMessage.team_id == team_id).order_by(TeamMessage.created_at.asc()).limit(limit).all()

    return [
        TeamMessageResponse(
            id=m.id,
            team_id=m.team_id,
            sender_id=m.sender_id,
            sender_name=m.sender.name,
            sender_avatar=m.sender.avatar_url,
            content=m.content,
            created_at=m.created_at
        )
        for m in messages
    ]
