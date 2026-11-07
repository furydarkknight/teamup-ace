import sys
import pickle
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

def train_model():
    csv_path = PROJECT_ROOT / "training" / "teamup_match_dataset.csv"
    if not csv_path.exists():
        print("Dataset CSV not found. Running export_dataset.py first...")
        from training.export_dataset import export_dataset
        export_dataset()

    print(f"Loading training data from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Exclude metadata columns and label
    meta_cols = ["user_id", "candidate_id", "event_id", "label_successful_team"]
    feature_cols = [c for c in df.columns if c not in meta_cols]

    X = df[feature_cols].values
    y = df["label_successful_team"].values

    print(f"Training RandomForestClassifier on {X.shape[0]} samples with {X.shape[1]} features...")
    model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=8)
    model.fit(X, y)

    model_dir = PROJECT_ROOT / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "matcher.pkl"

    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    print(f"[OK] Trained model successfully saved to: {model_path}")
    print("You can now set MATCHER=ml in your .env file to run with this ML model!")

if __name__ == "__main__":
    train_model()
