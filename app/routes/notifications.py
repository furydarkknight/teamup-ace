"""
Notification Center API Routes
In-app notification center & email-style notification log:
Matches, application updates, deadlines (T-3, T-1), team invites, and mentor replies.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.models_expansion import Notification

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(desc(Notification.created_at)).all()
    unread_count = sum(1 for n in notifs if not n.is_read)

    return {
        "unread_count": unread_count,
        "items": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "link": n.link,
                "type": n.notification_type,
                "is_read": n.is_read,
                "time": n.created_at.strftime("%b %d, %I:%M %p") if n.created_at else ""
            }
            for n in notifs
        ]
    }


@router.put("/{id}/read")
def mark_notification_read(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notif = db.query(Notification).filter(Notification.id == id, Notification.user_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"message": "Notification marked as read"}


@router.put("/read-all")
@router.post("/mark-all-read")
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notification).filter(Notification.user_id == current_user.id).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}
