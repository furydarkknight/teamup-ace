from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Invite, Team, TeamMember, Event, User
from app.auth import get_current_user
from app.schemas import InviteCreate, InviteUpdateStatus, InviteResponse, UserPublicResponse

router = APIRouter(prefix="/api/invites", tags=["Invites"])

@router.post("", response_model=InviteResponse)
def send_invite(
    data: InviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot invite yourself")

    receiver = db.query(User).filter(User.id == data.receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient user not found")

    event = db.query(Event).filter(Event.id == data.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # If team_id is provided, verify current user is in or leads that team
    team = None
    if data.team_id:
        team = db.query(Team).filter(Team.id == data.team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        # Check team size limit
        curr_members_count = len(team.members)
        if curr_members_count >= event.team_size_max:
            raise HTTPException(status_code=400, detail=f"Team is already full ({curr_members_count}/{event.team_size_max} members)")

    # Check for existing pending invite
    existing = db.query(Invite).filter(
        Invite.sender_id == current_user.id,
        Invite.receiver_id == data.receiver_id,
        Invite.event_id == data.event_id,
        Invite.status == "pending"
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already sent a pending invite to this teammate")

    invite = Invite(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        team_id=data.team_id,
        event_id=data.event_id,
        message=data.message.strip() if data.message else "Hey, let's team up for this hackathon!",
        proposed_role=data.proposed_role.strip() if data.proposed_role else "Teammate",
        status="pending"
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    return InviteResponse(
        id=invite.id,
        sender_id=current_user.id,
        sender=UserPublicResponse.from_orm(current_user),
        receiver_id=receiver.id,
        receiver=UserPublicResponse.from_orm(receiver),
        team_id=team.id if team else None,
        team_name=team.name if team else None,
        event_id=event.id,
        event_name=event.name,
        message=invite.message,
        proposed_role=invite.proposed_role,
        status=invite.status,
        created_at=invite.created_at
    )

@router.get("", response_model=List[InviteResponse])
def get_my_invites(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Invite).filter(
        (Invite.receiver_id == current_user.id) | (Invite.sender_id == current_user.id)
    ).order_by(Invite.created_at.desc())

    if status_filter and status_filter != "all":
        query = query.filter(Invite.status == status_filter)

    invites = query.all()
    results = []

    for inv in invites:
        results.append(InviteResponse(
            id=inv.id,
            sender_id=inv.sender_id,
            sender=UserPublicResponse.from_orm(inv.sender),
            receiver_id=inv.receiver_id,
            receiver=UserPublicResponse.from_orm(inv.receiver),
            team_id=inv.team_id,
            team_name=inv.team.name if inv.team else None,
            event_id=inv.event_id,
            event_name=inv.event.name if inv.event else None,
            message=inv.message,
            proposed_role=inv.proposed_role,
            status=inv.status,
            created_at=inv.created_at
        ))

    return results

@router.put("/{invite_id}", response_model=InviteResponse)
def respond_to_invite(
    invite_id: int,
    data: InviteUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")

    if invite.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only respond to invites sent to you")

    new_status = data.status.lower().strip()
    if new_status not in ["accepted", "declined"]:
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'declined'")

    invite.status = new_status

    if new_status == "accepted":
        # If team exists, add receiver to team
        if invite.team_id:
            team = db.query(Team).filter(Team.id == invite.team_id).first()
            if team:
                # Check if not already in team
                is_mem = db.query(TeamMember).filter(
                    TeamMember.team_id == team.id,
                    TeamMember.user_id == current_user.id
                ).first()
                if not is_mem and team.leader_id != current_user.id:
                    member = TeamMember(
                        team_id=team.id,
                        user_id=current_user.id,
                        role=invite.proposed_role or "Teammate"
                    )
                    db.add(member)
        else:
            # If no team existed, create a new team for this event pairing!
            new_team = Team(
                event_id=invite.event_id,
                name=f"Squad {invite.sender.name.split()[0]} & {current_user.name.split()[0]}",
                tagline="Built on TeamUp by ACE",
                leader_id=invite.sender_id,
                pitch=""
            )
            db.add(new_team)
            db.flush()

            # Add sender and receiver as members
            db.add(TeamMember(team_id=new_team.id, user_id=invite.sender_id, role="Team Lead"))
            db.add(TeamMember(team_id=new_team.id, user_id=current_user.id, role=invite.proposed_role or "Co-Founder"))
            invite.team_id = new_team.id

    db.commit()
    db.refresh(invite)

    return InviteResponse(
        id=invite.id,
        sender_id=invite.sender_id,
        sender=UserPublicResponse.from_orm(invite.sender),
        receiver_id=invite.receiver_id,
        receiver=UserPublicResponse.from_orm(invite.receiver),
        team_id=invite.team_id,
        team_name=invite.team.name if invite.team else None,
        event_id=invite.event_id,
        event_name=invite.event.name if invite.event else None,
        message=invite.message,
        proposed_role=invite.proposed_role,
        status=invite.status,
        created_at=invite.created_at
    )
