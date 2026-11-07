"""
ML Matcher using sentence-transformers or sklearn/custom model with safe fallback.
Models directory: models/ (or models/ace_teamup_model_v2/)

If model is missing or sentence_transformers not installed, falls back to RuleBasedMatcher.

Feature schema: see models/feature_schema.json (229 features).
Text profile encoding:
  Student: "skills: {skills}. interests: {interests}. project_experience: {projects}. bio: {bio}. preferred_roles: {roles}. experience_level: {exp}"
  Team:    "required_skills: {req}. preferred_skills: {pref}. interests: {interests}. preferred_roles: {roles}. preferred_experience: {exp}. collaboration_preference: {collab}"
"""

import os
from pathlib import Path
from typing import List, Any

from app.config import BASE_DIR
from matching.base import BaseMatcher, MatchResult
from matching.rule_based import RuleBasedMatcher

MODEL_DIR = BASE_DIR / "models"

class MLMatcher(BaseMatcher):
    """
    ML-based Matcher for TeamUp.
    Supports sentence-transformers embeddings (when available) or scikit-learn models,
    with a graceful fallback to RuleBasedMatcher.
    """

    def __init__(self):
        self.model = None
        self.fallback = RuleBasedMatcher()
        self._load_model()

    def _load_model(self):
        # Check if modules.json or model.safetensors exists in models/ or models/ace_teamup_model_v2/
        target_dir = None
        if (MODEL_DIR / "modules.json").exists():
            target_dir = MODEL_DIR
        elif (MODEL_DIR / "ace_teamup_model_v2" / "modules.json").exists():
            target_dir = MODEL_DIR / "ace_teamup_model_v2"

        if target_dir is None:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(str(target_dir))
            print(f"[MLMatcher] Loaded sentence-transformers model from {target_dir}")
        except ImportError:
            print("[MLMatcher] sentence_transformers not installed. Using rule-based fallback.")
        except Exception as e:
            print(f"[MLMatcher] Failed to load model: {e}. Using rule-based fallback.")

    @staticmethod
    def _student_text(student: Any) -> str:
        skills = ", ".join(str(s) for s in (getattr(student, 'skills', []) or []))
        interests = ", ".join(str(i) for i in (getattr(student, 'interests', []) or []))
        projects = "; ".join(str(p) for p in (getattr(student, 'project_experience', []) or []))
        bio = getattr(student, 'bio', '') or getattr(student, 'short_bio', '') or ""
        roles = ", ".join(str(r) for r in (getattr(student, 'preferred_roles', []) or []))
        exp = getattr(student, 'experience_level', 'Intermediate') or 'Intermediate'
        return f"skills: {skills}. interests: {interests}. project_experience: {projects}. bio: {bio}. preferred_roles: {roles}. experience_level: {exp}"

    @staticmethod
    def _team_text(team: Any) -> str:
        req = ", ".join(str(s) for s in (getattr(team, 'required_skills', []) or []))
        pref = ", ".join(str(s) for s in (getattr(team, 'preferred_skills', []) or []))
        interests = ", ".join(str(i) for i in (getattr(team, 'interests', []) or []))
        roles = ", ".join(str(r) for r in (getattr(team, 'preferred_roles', []) or []))
        exp = getattr(team, 'preferred_experience', 'Intermediate') or 'Intermediate'
        collab = getattr(team, 'collaboration_preference', '') or ""
        return f"required_skills: {req}. preferred_skills: {pref}. interests: {interests}. preferred_roles: {roles}. preferred_experience: {exp}. collaboration_preference: {collab}"

    @staticmethod
    def _cosine(a, b):
        import numpy as np
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _ml_scores(self, student_text: str, team_texts: list) -> list:
        all_texts = [student_text] + team_texts
        embeddings = self.model.encode(all_texts, convert_to_numpy=True)
        student_emb = embeddings[0]
        team_embs = embeddings[1:]
        return [self._cosine(student_emb, t_emb) for t_emb in team_embs]

    def match_student_to_teams(self, student: Any, teams: List[Any]) -> List[MatchResult]:
        student_members = set()
        student_id_str = getattr(student, 'student_id', None)
        if student_id_str:
            for t in teams:
                if student_id_str in (getattr(t, 'current_members', []) or []):
                    student_members.add(getattr(t, 'id', -1))

        eligible_teams = [
            t for t in teams
            if getattr(t, 'vacancies', 0) > 0 and getattr(t, 'id', -1) not in student_members
        ]

        if not eligible_teams:
            return []

        rule_results = {r.team_id: r for r in self.fallback.match_student_to_teams(student, eligible_teams)}

        if self.model is None:
            results = list(rule_results.values())
            for r in results:
                r.notes = "Rule-based scoring (ML model not loaded)"
            return sorted(results, key=lambda x: x.score, reverse=True)

        try:
            student_text = self._student_text(student)
            team_texts = [self._team_text(t) for t in eligible_teams]
            similarities = self._ml_scores(student_text, team_texts)
        except Exception as e:
            print(f"[MLMatcher] Encoding error: {e}")
            results = list(rule_results.values())
            for r in results:
                r.notes = f"Rule-based fallback (ML error: {e})"
            return sorted(results, key=lambda x: x.score, reverse=True)

        results = []
        for i, team in enumerate(eligible_teams):
            ml_score = int(min(98, max(30, round(similarities[i] * 100))))
            base = rule_results.get(team.id if hasattr(team, 'id') else None)
            reasons = list(base.reasons) if base else []
            reasons.insert(0, f"AI Semantic Fit: {ml_score}% neural profile alignment.")
            results.append(MatchResult(
                user_id=student.id,
                team_id=getattr(team, 'id', None),
                score=ml_score,
                reasons=reasons,
                complementary_skills=base.complementary_skills if base else [],
                shared_interests=base.shared_interests if base else [],
                missing_skills_covered=base.missing_skills_covered if base else [],
                notes="Scored by ace_teamup_model_v2 (sentence-transformers)"
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def match_team_to_students(self, team: Any, students: List[Any]) -> List[MatchResult]:
        team_member_ids = {m.user_id for m in (getattr(team, 'members', []) or [])}
        eligible = [s for s in students if s.id not in team_member_ids]

        if not eligible:
            return []

        rule_results = {r.user_id: r for r in self.fallback.match_team_to_students(team, eligible)}

        if self.model is None:
            results = list(rule_results.values())
            for r in results:
                r.notes = "Rule-based scoring (ML model not loaded)"
            return sorted(results, key=lambda x: x.score, reverse=True)

        try:
            team_text = self._team_text(team)
            student_texts = [self._student_text(s) for s in eligible]
            all_texts = [team_text] + student_texts
            embeddings = self.model.encode(all_texts, convert_to_numpy=True)
            team_emb = embeddings[0]
            student_embs = embeddings[1:]
            similarities = [self._cosine(team_emb, s_emb) for s_emb in student_embs]
        except Exception as e:
            print(f"[MLMatcher] Encoding error: {e}")
            results = list(rule_results.values())
            for r in results:
                r.notes = f"Rule-based fallback (ML error: {e})"
            return sorted(results, key=lambda x: x.score, reverse=True)

        results = []
        for i, student in enumerate(eligible):
            ml_score = int(min(98, max(30, round(similarities[i] * 100))))
            base = rule_results.get(student.id)
            reasons = list(base.reasons) if base else []
            reasons.insert(0, f"AI Semantic Fit: {ml_score}% neural candidate match.")
            results.append(MatchResult(
                user_id=student.id,
                team_id=getattr(team, 'id', None),
                score=ml_score,
                reasons=reasons,
                complementary_skills=base.complementary_skills if base else [],
                shared_interests=base.shared_interests if base else [],
                missing_skills_covered=base.missing_skills_covered if base else [],
                notes="Scored by ace_teamup_model_v2 (sentence-transformers)"
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def match(self, user: Any, event: Any, candidates: List[Any]) -> List[MatchResult]:
        results = self.fallback.match(user, event, candidates)
        return results
