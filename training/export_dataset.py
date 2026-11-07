import os
import sys
import csv
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models import User, Team
from matching.features import build_features

SCHEMA_PATH = PROJECT_ROOT / "models" / "feature_schema.json"

def export_student_team_dataset(output_path: str = "training/teamup_match_dataset.csv"):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    feature_names = schema["feature_names"]

    db = SessionLocal()
    students = db.query(User).filter(User.student_id.isnot(None)).all()
    teams = db.query(Team).all()

    student_lookup = {s.student_id: s for s in students}

    positive_pairs = []
    for team in teams:
        members = team.current_members or []
        for sid in members:
            s = student_lookup.get(sid)
            if s:
                positive_pairs.append((s, team, 1))

    print(f"Collected {len(positive_pairs)} positive student-team member pairs.")

    # Generate sampled negative pairs
    negative_pairs = []
    target_negs = len(positive_pairs)
    random.seed(42)

    while len(negative_pairs) < target_negs:
        s = random.choice(students)
        t = random.choice(teams)
        if s.student_id not in (t.current_members or []):
            negative_pairs.append((s, t, 0))

    all_pairs = positive_pairs + negative_pairs
    random.shuffle(all_pairs)

    csv_path = PROJECT_ROOT / output_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    header = ["student_id", "team_id"] + feature_names + ["label_successful_match"]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for s, t, label in all_pairs:
            feats = build_features(s, t)
            writer.writerow([s.student_id, t.team_id or t.id] + feats + [label])

    print(f"Exported {len(all_pairs)} samples with {len(feature_names)} features to {csv_path}")
    db.close()

if __name__ == "__main__":
    export_student_team_dataset()
