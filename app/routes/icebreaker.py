from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.icebreaker import get_icebreaker_challenge

router = APIRouter(prefix="/api/icebreaker", tags=["Icebreaker"])

@router.get("/{partner_id}")
def get_user_icebreaker(
    partner_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if partner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot start an icebreaker with yourself")

    partner = db.query(User).filter(User.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Teammate not found")

    return get_icebreaker_challenge(current_user, partner)
