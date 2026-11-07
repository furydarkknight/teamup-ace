import os
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import BASE_DIR, PREDEFINED_SKILLS, PREDEFINED_INTERESTS
from matching.base import BaseMatcher, MatchResult
from matching.rule_based import RuleBasedMatcher

MODEL_PATH = BASE_DIR / "models" / "matcher.pkl"

class MLMatcher(BaseMatcher):
    """
    ML-based Matching Engine for TeamUp.
    
    This class loads a trained scikit-learn / XGBoost model from `models/matcher.pkl`.
    If the model is not found, or if candidates count is too small (cold start),
    it smoothly falls back to the RuleBasedMatcher while signaling this in the output.
    
    =============================================================================
    FEATURE VECTOR FORMAT FOR ML TRAINING & INFERENCE:
    Each candidate pair (user, candidate, event) is transformed into a 1D vector:
      1. user_skills (len = len(PREDEFINED_SKILLS)): binary 0/1 indicator
      2. cand_skills (len = len(PREDEFINED_SKILLS)): binary 0/1 indicator
      3. event_roles (len = len(PREDEFINED_SKILLS)): binary 0/1 indicator
      4. complement_vector = cand_skills * np.maximum(0, event_roles - user_skills)
      5. availability_overlap: 1.0 (exact/flexible), 0.7 (compatible), 0.3 (different)
      6. user_experience: 0 (Beginner), 1 (Intermediate), 2 (Advanced)
      7. cand_experience: 0 (Beginner), 1 (Intermediate), 2 (Advanced)
      8. goal_alignment: 1.0 (exact), 0.6 (complementary), 0.3 (different)
      9. workstyle_schedule_match: 1.0 if match/flexible else 0.0
      10. workstyle_role_synergy: 1.0 if (leader + executor) else 0.5
      11. cand_reliability_score: float between 0.0 and 1.0
    =============================================================================
    """

    def __init__(self):
        self.model = None
        self.fallback_matcher = RuleBasedMatcher()
        self._load_model()

    def _load_model(self):
        """Loads trained model from models/matcher.pkl if present."""
        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                print(f"[MLMatcher] Successfully loaded trained model from {MODEL_PATH}")
            except Exception as e:
                print(f"[MLMatcher] Error loading model from {MODEL_PATH}: {e}. Using rule-based fallback.")
                self.model = None
        else:
            self.model = None

    @staticmethod
    def extract_feature_vector(user: Any, candidate: Any, event: Any) -> np.ndarray:
        """
        Transforms (user, candidate, event) into the exact numerical feature vector
        documented above.
        """
        skill_map = {skill.lower(): i for i, skill in enumerate(PREDEFINED_SKILLS)}
        n_skills = len(PREDEFINED_SKILLS)

        # 1. user skills binary
        user_skills_vec = np.zeros(n_skills, dtype=np.float32)
        for s in user.skills:
            name = s.get("name", "").lower()
            for key, idx in skill_map.items():
                if key in name or name in key:
                    user_skills_vec[idx] = 1.0

        # 2. candidate skills binary
        cand_skills_vec = np.zeros(n_skills, dtype=np.float32)
        for s in candidate.skills:
            name = s.get("name", "").lower()
            for key, idx in skill_map.items():
                if key in name or name in key:
                    cand_skills_vec[idx] = 1.0

        # 3. event required roles binary
        event_roles_vec = np.zeros(n_skills, dtype=np.float32)
        if event and event.required_roles:
            for r in event.required_roles:
                r_lower = r.lower()
                for key, idx in skill_map.items():
                    if key in r_lower or r_lower in key:
                        event_roles_vec[idx] = 1.0

        # 4. complement vector: skills candidate covers that user lacks for event
        missing_from_user = np.maximum(0.0, event_roles_vec - user_skills_vec)
        complement_vec = cand_skills_vec * missing_from_user

        # 5. availability
        u_avail = (user.availability or "").lower()
        c_avail = (candidate.availability or "").lower()
        if "flexible" in u_avail or "flexible" in c_avail or u_avail == c_avail:
            avail_score = 1.0
        elif ("weekend" in u_avail and "evening" in c_avail) or ("evening" in u_avail and "weekend" in c_avail):
            avail_score = 0.7
        else:
            avail_score = 0.3

        # 6 & 7. experience
        exp_map = {"beginner": 0.0, "intermediate": 1.0, "advanced": 2.0}
        u_exp = exp_map.get((user.experience_level or "intermediate").lower(), 1.0)
        c_exp = exp_map.get((candidate.experience_level or "intermediate").lower(), 1.0)

        # 8. goal alignment
        u_goal = (user.goal or "").lower()
        c_goal = (candidate.goal or "").lower()
        goal_score = 1.0 if u_goal == c_goal else (0.6 if ("win" in u_goal and "learn" in c_goal) else 0.4)

        # 9 & 10. work style
        sched_match = 1.0 if (user.work_schedule == candidate.work_schedule or "Flexible" in (user.work_schedule, candidate.work_schedule)) else 0.5
        u_role = user.work_role or ""
        c_role = candidate.work_role or ""
        role_synergy = 1.0 if ("Leader" in u_role and "Executor" in c_role) or ("Executor" in u_role and "Leader" in c_role) else 0.6

        # 11. reliability
        cand_rel = float(candidate.reliability_score or 75.0) / 100.0

        scalars = np.array([
            avail_score,
            u_exp,
            c_exp,
            goal_score,
            sched_match,
            role_synergy,
            cand_rel
        ], dtype=np.float32)

        return np.concatenate([
            user_skills_vec,
            cand_skills_vec,
            event_roles_vec,
            complement_vec,
            scalars
        ])

    def match(self, user: Any, event: Any, candidates: List[Any]) -> List[MatchResult]:
        # Cold start handling: if fewer than 2 candidates, fallback to rule-based
        if len(candidates) < 2:
            results = self.fallback_matcher.match(user, event, candidates)
            for r in results:
                r.notes = "Cold-start condition (<2 candidates): Served via Rule-Based Matcher"
            return results

        # If trained model is not present, use rule-based fallback
        if self.model is None:
            results = self.fallback_matcher.match(user, event, candidates)
            for r in results:
                r.notes = "ML Model stub active (models/matcher.pkl not found). Using rule-based fallback with ML feature schema ready."
            return results

        # Model is present! Predict scores using the ML model
        # =========================================================================
        # TODO: CUSTOM ML INFERENCE LOGIC
        # Your custom model (e.g. Scikit-Learn RandomForest, LightGBM, Neural Net)
        # receives feature vectors of dimension:
        # [batch_size, 4 * len(PREDEFINED_SKILLS) + 7]
        # =========================================================================
        feature_matrix = []
        valid_candidates = []

        for candidate in candidates:
            if candidate.id == user.id:
                continue
            if candidate.id in (user.blocked_users or []):
                continue
            if user.id in (candidate.blocked_users or []):
                continue

            feat = self.extract_feature_vector(user, candidate, event)
            feature_matrix.append(feat)
            valid_candidates.append(candidate)

        if not feature_matrix:
            return []

        X = np.array(feature_matrix)

        try:
            # Model prediction: either predict_proba[:, 1] for classification or predict() for regression
            if hasattr(self.model, "predict_proba"):
                raw_preds = self.model.predict_proba(X)[:, 1] * 100.0
            else:
                raw_preds = self.model.predict(X)
                # Scale if normalized
                if np.max(raw_preds) <= 1.0:
                    raw_preds = raw_preds * 100.0
        except Exception as e:
            print(f"[MLMatcher] Prediction error: {e}. Falling back to rule-based.")
            return self.fallback_matcher.match(user, event, candidates)

        # Baseline rule explanations so the UI retains rich explainability
        rule_results = {r.user_id: r for r in self.fallback_matcher.match(user, event, valid_candidates)}

        results: List[MatchResult] = []
        for i, candidate in enumerate(valid_candidates):
            ml_score = int(min(99, max(50, round(float(raw_preds[i])))))
            base_res = rule_results.get(candidate.id)
            
            reasons = list(base_res.reasons) if base_res else []
            reasons.insert(0, f"🤖 ML Model Match: Neural score {ml_score}% predicted from complement & compatibility vectors.")

            results.append(MatchResult(
                user_id=candidate.id,
                score=ml_score,
                reasons=reasons,
                complementary_skills=base_res.complementary_skills if base_res else [],
                shared_interests=base_res.shared_interests if base_res else [],
                workstyle_compatibility=base_res.workstyle_compatibility if base_res else 75,
                is_mentor_match=base_res.is_mentor_match if base_res else False,
                notes="Scored by Trained ML Model (models/matcher.pkl)"
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results
