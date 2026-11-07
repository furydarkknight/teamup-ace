import os
import sys
import csv
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models import User, Event, Team, TeamMember, Invite
from app.config import PREDEFINED_SKILLS
from matching.ml_matcher import MLMatcher

def export_dataset(output_path: str = "training/teamup_match_dataset.csv"):
    db = SessionLocal()
    users = db.query(User).all()
    events = db.query(Event).all()
    teams = db.query(Team).all()
    invites = db.query(Invite).all()

    # Pre-build pairs of users who successfully formed teams or accepted invites
    success_pairs = set()
    for team in teams:
        members = [m.user_id for m in team.members]
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                success_pairs.add((members[i], members[j]))
                success_pairs.add((members[j], members[i]))

    for inv in invites:
        if inv.status == "accepted":
            success_pairs.add((inv.sender_id, inv.receiver_id))
            success_pairs.add((inv.receiver_id, inv.sender_id))

    # Build CSV header
    feature_names = []
    for s in PREDEFINED_SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("&", "and")
        feature_names.append(f"user_has_{s_clean}")
    for s in PREDEFINED_SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("&", "and")
        feature_names.append(f"cand_has_{s_clean}")
    for s in PREDEFINED_SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("&", "and")
        feature_names.append(f"event_needs_{s_clean}")
    for s in PREDEFINED_SKILLS:
        s_clean = s.lower().replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("&", "and")
        feature_names.append(f"complement_{s_clean}")

    scalar_names = [
        "availability_overlap",
        "user_experience",
        "cand_experience",
        "goal_alignment",
        "workstyle_schedule_match",
        "workstyle_role_synergy",
        "cand_reliability_score"
    ]
    header = ["user_id", "candidate_id", "event_id"] + feature_names + scalar_names + ["label_successful_team"]

    rows = []
    matcher = MLMatcher()

    for event in events:
        for i, user in enumerate(users):
            for candidate in users[i+1:]:
                # Extract numerical features
                vec = matcher.extract_feature_vector(user, candidate, event)
                
                # Check ground truth label
                is_success = 1 if (user.id, candidate.id) in success_pairs else 0
                
                # If synthetic enrichment is needed when few real pairs exist:
                # Complementary skill overlap + schedule match yields positive signal
                if not is_success:
                    complement_sum = vec[3*len(PREDEFINED_SKILLS) : 4*len(PREDEFINED_SKILLS)].sum()
                    if complement_sum >= 1.0 and vec[-7] >= 0.7:  # availability >= 0.7
                        is_success = 1

                row = [user.id, candidate.id, event.id] + list(vec) + [is_success]
                rows.append(row)

    out_file = PROJECT_ROOT / output_path
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"[OK] Exported {len(rows)} training samples with {len(header)-4} feature columns to: {out_file}")
    db.close()

if __name__ == "__main__":
    export_dataset()
