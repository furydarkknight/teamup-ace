import json
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, StudentProfile, generate_next_student_id
from app.auth import (
    hash_password, verify_password, create_access_token,
    check_is_verified_email, get_current_user
)
from app.schemas import SignUpRequest, LoginRequest, TokenResponse, UserPublicResponse, ForgotPasswordRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered. Please sign in instead.")

    is_verified = check_is_verified_email(email_clean)
    hashed = hash_password(data.password)

    # Initial avatar
    avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={data.name.replace(' ', '')}"
    
    # Safe sequential student ID (e.g. S1001)
    next_student_id = generate_next_student_id(db)

    skills_list = data.skills or []
    prof_dict = data.skill_proficiency or {s: 3 for s in skills_list}
    interests_list = data.interests or []
    roles_list = data.preferred_roles or []
    projects_list = data.project_experience or []

    new_user = User(
        student_id=next_student_id,
        email=email_clean,
        hashed_password=hashed,
        is_verified=is_verified,
        name=data.name.strip(),
        college=data.college.strip(),
        city=data.city.strip() if data.city else "Delhi",
        year=data.year.strip() if data.year else "3rd Year",
        avatar_url=avatar_url,
        bio=data.bio or "",
        short_bio=(data.bio or "")[:200],
        skills_json=json.dumps(skills_list),
        skill_proficiency_json=json.dumps(prof_dict),
        interests_json=json.dumps(interests_list),
        preferred_roles_json=json.dumps(roles_list),
        experience_level=data.experience_level or "Intermediate",
        availability=data.availability or "Full-time",
        preferred_team_size=data.preferred_team_size or 4,
        collaboration_preference=data.collaboration_preference or "",
        project_experience_json=json.dumps(projects_list),
        reliability_score=85.0 if is_verified else 75.0,
        ratings_count=0,
        role="student",
        roles_json=json.dumps(["student"])
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Also set username
    new_user.username = f"{data.name.lower().replace(' ', '')}{new_user.id}"

    # Create linked StudentProfile
    profile_record = StudentProfile(
        user_id=new_user.id,
        student_id=new_user.student_id,
        college=new_user.college,
        city=new_user.city,
        year=new_user.year,
        bio=new_user.bio or "",
        skills_json=new_user.skills_json,
        skill_proficiency_json=new_user.skill_proficiency_json,
        interests_json=new_user.interests_json,
        preferred_roles_json=new_user.preferred_roles_json,
        experience_level=new_user.experience_level,
        availability=new_user.availability,
        preferred_team_size=new_user.preferred_team_size,
        collaboration_preference=new_user.collaboration_preference,
        project_experience_json=new_user.project_experience_json
    )
    db.add(profile_record)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserPublicResponse.from_orm(new_user).dict()
    }

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserPublicResponse.from_orm(user).dict()
    }

@router.get("/me", response_model=UserPublicResponse)
def get_me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email_clean = req.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    reset_token = f"reset_{secrets.token_hex(16)}"
    print(f"\n[Mock Password Reset] Requested for: {email_clean}")
    print(f"[Mock Password Reset] One-Time Reset Token: {reset_token}\n")
    return {
        "message": f"If an account exists for {email_clean}, password reset instructions have been logged.",
        "mock_token": reset_token
    }


@router.post("/verify-college")
def verify_college_email(
    college_email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allow user to optionally verify later with their college email address."""
    clean = college_email.strip().lower()
    if not check_is_verified_email(clean):
        raise HTTPException(status_code=400, detail="Must provide an institutional email ending in .edu, .ac.in, or .edu.in")
    
    current_user.is_verified = True
    db.commit()
    db.refresh(current_user)
    return {"message": "College credentials verified successfully! Verified badge unlocked.", "is_verified": True}
