from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import OpenSeat, SeatApplication, Team, Event, User, TeamMember
from app.auth import get_current_user, get_current_verified_user
from app.schemas import (
    OpenSeatCreate, OpenSeatResponse, SeatApplyRequest,
    SeatApplicationResponse, UserPublicResponse
)

router = APIRouter(prefix="/api", tags=["Open Seats"])

@router.post("/seats", response_model=OpenSeatResponse)
def create_open_seat(
    data: OpenSeatCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = db.query(Team).filter(Team.id == data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team leader can post an open seat")

    new_seat = OpenSeat(
        team_id=data.team_id,
        event_id=data.event_id,
        role_title=data.role_title.strip(),
        short_note=data.short_note.strip() if data.short_note else "",
        status="open"
    )
    new_seat.required_skills = data.required_skills

    db.add(new_seat)
    db.commit()
    db.refresh(new_seat)

    return OpenSeatResponse(
        id=new_seat.id,
        team_id=team.id,
        team_name=team.name,
        event_id=new_seat.event_id,
        role_title=new_seat.role_title,
        required_skills=new_seat.required_skills,
        short_note=new_seat.short_note,
        status=new_seat.status,
        created_at=new_seat.created_at,
        applications_count=0,
        leader_name=team.leader.name
    )

@router.get("/events/{event_id}/seats", response_model=List[OpenSeatResponse])
def get_event_seats(event_id: int, db: Session = Depends(get_db)):
    seats = db.query(OpenSeat).filter(OpenSeat.event_id == event_id).order_by(OpenSeat.created_at.desc()).all()
    results = []

    for seat in seats:
        apps_count = db.query(SeatApplication).filter(SeatApplication.seat_id == seat.id).count()
        results.append(OpenSeatResponse(
            id=seat.id,
            team_id=seat.team.id,
            team_name=seat.team.name,
            event_id=seat.event_id,
            role_title=seat.role_title,
            required_skills=seat.required_skills,
            short_note=seat.short_note,
            status=seat.status,
            created_at=seat.created_at,
            applications_count=apps_count,
            leader_name=seat.team.leader.name
        ))

    return results

@router.post("/seats/{seat_id}/apply")
def apply_to_seat(
    seat_id: int,
    data: SeatApplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    seat = db.query(OpenSeat).filter(OpenSeat.id == seat_id).first()
    if not seat or seat.status != "open":
        raise HTTPException(status_code=400, detail="Seat is no longer available")

    # Check if already a member of this team
    is_member = db.query(TeamMember).filter(
        TeamMember.team_id == seat.team_id,
        TeamMember.user_id == current_user.id
    ).first()
    if is_member or seat.team.leader_id == current_user.id:
        raise HTTPException(status_code=400, detail="You are already in this team")

    # Check existing application
    existing_app = db.query(SeatApplication).filter(
        SeatApplication.seat_id == seat_id,
        SeatApplication.user_id == current_user.id
    ).first()
    if existing_app:
        raise HTTPException(status_code=400, detail="You have already applied for this role")

    new_app = SeatApplication(
        seat_id=seat_id,
        user_id=current_user.id,
        note=data.note.strip() if data.note else "Interested in joining your team!",
        status="pending"
    )
    db.add(new_app)
    db.commit()

    return {"message": "Application submitted successfully!", "status": "pending"}

@router.get("/seats/{seat_id}/applications", response_model=List[SeatApplicationResponse])
def get_seat_applications(
    seat_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    seat = db.query(OpenSeat).filter(OpenSeat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if seat.team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team leader can view seat applications")

    apps = db.query(SeatApplication).filter(SeatApplication.seat_id == seat_id).all()
    results = []
    for a in apps:
        results.append(SeatApplicationResponse(
            id=a.id,
            user_id=a.user_id,
            user=UserPublicResponse.from_orm(a.user),
            note=a.note,
            status=a.status,
            created_at=a.created_at
        ))
    return results

@router.put("/seats/applications/{app_id}")
def update_application_status(
    app_id: int,
    status_update: str, # "accepted" or "rejected"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app = db.query(SeatApplication).filter(SeatApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    seat = app.seat
    if seat.team.leader_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only team leader can respond to applications")

    status_clean = status_update.lower().strip()
    if status_clean not in ["accepted", "rejected"]:
        raise HTTPException(status_code=400, detail="Status must be 'accepted' or 'rejected'")

    app.status = status_clean

    if status_clean == "accepted":
        # Add user to team
        new_member = TeamMember(
            team_id=seat.team_id,
            user_id=app.user_id,
            role=seat.role_title
        )
        db.add(new_member)
        seat.status = "filled"

    db.commit()
    return {"message": f"Application marked as {status_clean}", "status": status_clean}
