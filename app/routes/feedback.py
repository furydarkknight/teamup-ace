from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Feedback, User, Team, Event, TeamMember
from app.auth import get_current_user
from app.schemas import FeedbackCreate

router = APIRouter(prefix="/api/feedback", tags=["Peer Feedback & Reliability"])

@router.post("")
def submit_peer_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.to_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot rate yourself")

    target_user = db.query(User).filter(User.id == data.to_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Teammate not found")

    team = db.query(Team).filter(Team.id == data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Verify both users were part of this team
    is_author_member = any(m.user_id == current_user.id for m in team.members) or team.leader_id == current_user.id
    is_target_member = any(m.user_id == target_user.id for m in team.members) or team.leader_id == target_user.id

    if not (is_author_member and is_target_member):
        raise HTTPException(status_code=403, detail="You can only provide peer feedback to teammates on your team")

    # Star rating to points (1-5 -> 30-100)
    rating_map = {1: 30.0, 2: 50.0, 3: 70.0, 4: 85.0, 5: 100.0}
    base_points = rating_map.get(max(1, min(5, data.rating)), 85.0)

    # Bonus for positive tags
    tag_bonus = min(10.0, len(data.tags) * 2.5)
    score_for_this_review = min(100.0, base_points + tag_bonus)

    # Calculate new rolling average reliability score
    curr_count = target_user.ratings_count or 0
    curr_score = target_user.reliability_score if curr_count > 0 else 80.0 # start baseline

    new_score = ((curr_score * curr_count) + score_for_this_review) / (curr_count + 1)
    target_user.reliability_score = round(new_score, 1)
    target_user.ratings_count = curr_count + 1

    feedback = Feedback(
        event_id=data.event_id,
        team_id=data.team_id,
        from_user_id=current_user.id,
        to_user_id=data.to_user_id,
        rating=data.rating,
        comment=data.comment.strip() if data.comment else ""
    )
    feedback.tags = data.tags

    db.add(feedback)
    db.commit()

    return {
        "message": "Peer feedback submitted successfully!",
        "new_reliability_score": target_user.reliability_score,
        "ratings_count": target_user.ratings_count
    }
