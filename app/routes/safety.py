from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Report, User
from app.auth import get_current_user
from app.schemas import ReportCreate, BlockUserRequest

router = APIRouter(prefix="/api", tags=["Safety"])

@router.post("/report")
def report_user(
    data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.reported_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot report yourself")

    target = db.query(User).filter(User.id == data.reported_user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    new_report = Report(
        reporter_id=current_user.id,
        reported_user_id=data.reported_user_id,
        reason=data.reason.strip(),
        details=data.details.strip() if data.details else ""
    )
    db.add(new_report)
    db.commit()

    return {"message": "Report logged confidentially. Our moderation safety team will review it."}

@router.post("/block")
def block_user(
    data: BlockUserRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot block yourself")

    target = db.query(User).filter(User.id == data.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    blocked = list(current_user.blocked_users or [])
    if data.user_id not in blocked:
        blocked.append(data.user_id)
        current_user.blocked_users = blocked
        db.commit()

    return {"message": f"User {target.name} has been blocked. They will no longer appear in your AI match feed."}
