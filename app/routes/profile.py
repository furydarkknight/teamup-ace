from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.schemas import UserPublicResponse, ProfileUpdateRequest
from app.config import (
    PREDEFINED_SKILLS, PROFICIENCY_LEVELS, PREDEFINED_INTERESTS,
    AVAILABILITY_OPTIONS, GOAL_OPTIONS, WORK_STYLES
)

router = APIRouter(prefix="/api/profile", tags=["Profile"])

@router.get("", response_model=UserPublicResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("", response_model=UserPublicResponse)
def update_my_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    update_data = data.dict(exclude_unset=True)
    
    if "skills" in update_data and update_data["skills"] is not None:
        current_user.skills = update_data.pop("skills")
    
    if "interests" in update_data and update_data["interests"] is not None:
        current_user.interests = update_data.pop("interests")

    for field, val in update_data.items():
        if hasattr(current_user, field) and val is not None:
            setattr(current_user, field, val)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/options")
def get_profile_options():
    return {
        "skills": PREDEFINED_SKILLS,
        "proficiency_levels": PROFICIENCY_LEVELS,
        "interests": PREDEFINED_INTERESTS,
        "availability": AVAILABILITY_OPTIONS,
        "goals": GOAL_OPTIONS,
        "work_styles": WORK_STYLES
    }

@router.get("/{user_id}", response_model=UserPublicResponse)
def get_user_public_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
