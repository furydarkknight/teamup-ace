from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import (
    hash_password, verify_password, create_access_token,
    check_is_verified_email, get_current_user
)
from app.schemas import SignUpRequest, LoginRequest, TokenResponse, UserPublicResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=TokenResponse)
def signup(data: SignUpRequest, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    is_verified = check_is_verified_email(email_clean)
    hashed = hash_password(data.password)

    # Initial avatar
    avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={data.name.replace(' ', '')}"

    new_user = User(
        email=email_clean,
        hashed_password=hashed,
        is_verified=is_verified,
        name=data.name.strip(),
        college=data.college.strip(),
        city=data.city.strip() if data.city else "Delhi",
        year=data.year.strip() if data.year else "3rd Year",
        avatar_url=avatar_url,
        skills_json="[]",
        interests_json="[]",
        reliability_score=0.0,
        ratings_count=0
    )
    db.add(new_user)
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
