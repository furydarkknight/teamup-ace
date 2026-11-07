from typing import List, Any
from matching.base import BaseMatcher, MatchResult
from matching.weights import (
    SKILL_GAP_COVERAGE_WEIGHT, INTEREST_OVERLAP_WEIGHT, ROLE_FIT_WEIGHT,
    EXPERIENCE_FIT_WEIGHT, AVAILABILITY_WEIGHT, COLLABORATION_WEIGHT,
    TEAM_SIZE_FIT_WEIGHT, MIN_SCORE, MAX_SCORE
)

EXP_ORDER = {"beginner": 0, "intermediate": 1, "advanced": 2}
COLLAB_FLEXIBLE = "comfortable with both"  # partial match keyword

class RuleBasedMatcher(BaseMatcher):
    """
    Rule-based matching engine v2 - updated for new data model.
    
    Student->Student (event-based): legacy compat, used by existing event match feed.
    Student->Team: core new direction.
    Team->Student: reverse direction for team leads.

    Weights loaded from matching/weights.py for easy tuning.
    """

    def _skill_gap_score(self, student_skills: dict, team_requirements: dict, team_required_list: list) -> tuple:
        """
        Returns (score 0-1, covered_skills list, missing_skills list).
        student_skills: {skill: proficiency_level 1-5}
        team_requirements: {skill: min_level_needed 1-5}
        team_required_list: list of required skill names
        """
        all_required = set(team_required_list or [])
        if team_requirements:
            for s in team_requirements:
                all_required.add(s)

        if not all_required:
            return 0.5, [], []

        covered = []
        missing = []
        total_points = 0.0
        max_points = 0.0

        for skill in all_required:
            min_level = team_requirements.get(skill, 1) if team_requirements else 1
            max_points += 1.0

            student_level = None
            for sk, lv in (student_skills or {}).items():
                if sk.lower() == skill.lower():
                    student_level = lv
                    break

            if student_level is None:
                missing.append(skill)
            elif student_level >= min_level:
                covered.append(skill)
                total_points += 1.0
            else:
                ratio = student_level / max(min_level, 1)
                total_points += ratio * 0.7
                missing.append(skill)

        score = total_points / max(max_points, 1.0)
        return score, covered, missing

    @staticmethod
    def _interest_jaccard(a_interests: list, b_interests: list) -> tuple:
        a_set = {str(x).lower() for x in (a_interests or [])}
        b_set = {str(x).lower() for x in (b_interests or [])}
        if not a_set and not b_set:
            return 0.5, []
        shared = a_set & b_set
        union = a_set | b_set
        shared_display = [x for x in (a_interests or []) if str(x).lower() in shared]
        return len(shared) / max(len(union), 1), shared_display

    @staticmethod
    def _role_fit(student_roles: list, team_roles: list) -> tuple:
        if not student_roles or not team_roles:
            return 0.5, []
        s_set = {str(r).lower() for r in student_roles}
        t_set = {str(r).lower() for r in team_roles}
        matched = s_set & t_set
        matched_display = [r for r in student_roles if str(r).lower() in matched]
        score = len(matched) / max(len(t_set), 1)
        return min(score, 1.0), matched_display

    @staticmethod
    def _experience_fit(student_exp: str, team_preferred_exp: str) -> float:
        s = EXP_ORDER.get((student_exp or "intermediate").lower(), 1)
        t = EXP_ORDER.get((team_preferred_exp or "intermediate").lower(), 1)
        diff = abs(s - t)
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.5
        return 0.1

    @staticmethod
    def _availability_match(student_avail: str, team_avail: str) -> float:
        s = (student_avail or "").lower()
        t = (team_avail or "").lower()
        if s == t:
            return 1.0
        if "full" in s or "full" in t:
            return 0.7
        return 0.3

    @staticmethod
    def _collab_match(student_collab: str, team_collab: str) -> float:
        s = (student_collab or "").lower()
        t = (team_collab or "").lower()
        if not s or not t:
            return 0.5
        if s == t:
            return 1.0
        if COLLAB_FLEXIBLE in s or COLLAB_FLEXIBLE in t:
            return 0.7
        return 0.2

    @staticmethod
    def _size_fit(student_pref_size: int, team_total_size: int) -> float:
        diff = abs((student_pref_size or 4) - (team_total_size or 4))
        if diff == 0:
            return 1.0
        elif diff <= 1:
            return 0.7
        elif diff <= 2:
            return 0.4
        return 0.1

    def _score_student_team(self, student: Any, team: Any) -> MatchResult:
        student_prof = getattr(student, 'skill_proficiency', {}) or {}
        team_reqs = getattr(team, 'skill_requirements', {}) or {}
        team_req_list = getattr(team, 'required_skills', []) or []

        gap_score, covered_skills, missing_skills = self._skill_gap_score(
            student_prof, team_reqs, team_req_list
        )

        student_ints = getattr(student, 'interests', []) or []
        team_ints = getattr(team, 'interests', []) or []
        interest_score, shared_interests = self._interest_jaccard(student_ints, team_ints)

        student_roles = getattr(student, 'preferred_roles', []) or []
        team_roles = getattr(team, 'preferred_roles', []) or []
        role_score, matched_roles = self._role_fit(student_roles, team_roles)

        exp_score = self._experience_fit(
            getattr(student, 'experience_level', 'Intermediate'),
            getattr(team, 'preferred_experience', 'Intermediate')
        )

        avail_score = self._availability_match(
            getattr(student, 'availability', 'Full-time'),
            getattr(team, 'availability', 'Full-time')
        )

        collab_score = self._collab_match(
            getattr(student, 'collaboration_preference', ''),
            getattr(team, 'collaboration_preference', '')
        )

        team_total = getattr(team, 'current_team_size', 1) + getattr(team, 'vacancies', 3)
        size_score = self._size_fit(
            getattr(student, 'preferred_team_size', 4), team_total
        )

        raw = (
            gap_score      * SKILL_GAP_COVERAGE_WEIGHT +
            interest_score * INTEREST_OVERLAP_WEIGHT +
            role_score     * ROLE_FIT_WEIGHT +
            exp_score      * EXPERIENCE_FIT_WEIGHT +
            avail_score    * AVAILABILITY_WEIGHT +
            collab_score   * COLLABORATION_WEIGHT +
            size_score     * TEAM_SIZE_FIT_WEIGHT
        )

        final_score = int(min(MAX_SCORE, max(MIN_SCORE, round(raw * 100))))

        reasons = []
        total_req_count = len(set(list(team_req_list) + list(team_reqs.keys())))
        if covered_skills:
            reasons.append(f"Skills Match: You cover {len(covered_skills)}/{max(total_req_count, 1)} required skills ({', '.join(covered_skills[:3])}).")
        elif missing_skills:
            reasons.append(f"Skill Gap: Team needs {', '.join(missing_skills[:3])} - great learning opportunity.")

        if shared_interests and interest_score >= 0.15:
            reasons.append(f"Shared Interests: Both into {', '.join(shared_interests[:3])}.")

        if matched_roles and role_score > 0:
            reasons.append(f"Role Fit: Your roles ({', '.join(matched_roles[:2])}) align with team openings.")

        exp_txt = {1.0: "exact", 0.5: "adjacent", 0.1: "different"}.get(exp_score, "close")
        reasons.append(f"Experience: {exp_txt.capitalize()} fit (You: {getattr(student,'experience_level','?')}, Team seeks: {getattr(team,'preferred_experience','?')}).")

        if avail_score >= 0.7:
            reasons.append(f"Availability: Compatible ({getattr(student,'availability','?')} <-> {getattr(team,'availability','?')}).")

        if collab_score >= 0.7:
            reasons.append(f"Collaboration: Aligned working culture.")

        breakdown = {
            "skills": round(gap_score * 100),
            "interests": round(interest_score * 100),
            "roles": round(role_score * 100),
            "experience": round(exp_score * 100),
            "availability": round(avail_score * 100),
            "collaboration": round(collab_score * 100),
            "team_size": round(size_score * 100)
        }

        return MatchResult(
            user_id=student.id,
            team_id=getattr(team, 'id', None),
            score=final_score,
            reasons=reasons,
            complementary_skills=covered_skills,
            shared_interests=shared_interests,
            missing_skills_covered=covered_skills,
            breakdown=breakdown,
            engine="Rule-based engine"
        )

    def match_student_to_teams(self, student: Any, teams: List[Any]) -> List[MatchResult]:
        results = []
        student_members = set()
        student_id_str = getattr(student, 'student_id', None)
        if student_id_str:
            for t in teams:
                if student_id_str in (getattr(t, 'current_members', []) or []):
                    student_members.add(getattr(t, 'id', -1))

        for team in teams:
            tid = getattr(team, 'id', -1)
            if tid in student_members:
                continue
            if getattr(team, 'vacancies', 0) <= 0:
                continue
            if hasattr(student, 'blocked_users') and hasattr(team, 'leader') and team.leader:
                if team.leader.id in (student.blocked_users or []):
                    continue

            result = self._score_student_team(student, team)
            results.append(result)

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def match_team_to_students(self, team: Any, students: List[Any]) -> List[MatchResult]:
        results = []
        team_member_ids = {m.user_id for m in (getattr(team, 'members', []) or [])}

        for student in students:
            if student.id in team_member_ids:
                continue
            if getattr(team, 'vacancies', 0) <= 0:
                continue

            result = self._score_student_team(student, team)
            results.append(result)

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def match(self, user: Any, event: Any, candidates: List[Any]) -> List[MatchResult]:
        """
        Legacy event-based student-to-student match.
        Used by the original event match feed.
        """
        results = []

        user_skills_raw = user.skills if hasattr(user, 'skills') else []
        user_skill_names = set(str(s).lower() for s in user_skills_raw)
        event_required_roles = []
        if event and hasattr(event, 'required_roles'):
            event_required_roles = [str(r).strip() for r in (event.required_roles or [])]

        user_missing_roles = []
        for role in event_required_roles:
            role_lower = role.lower()
            if not any(us in role_lower or role_lower in us for us in user_skill_names):
                user_missing_roles.append(role)

        for candidate in candidates:
            if candidate.id == user.id:
                continue
            if candidate.id in (getattr(user, 'blocked_users', []) or []):
                continue
            if user.id in (getattr(candidate, 'blocked_users', []) or []):
                continue

            cand_skills_raw = candidate.skills if hasattr(candidate, 'skills') else []
            cand_skill_names = set(str(s).lower() for s in cand_skills_raw)

            # 1. Complementary skills (35%)
            covered_missing = []
            for role in user_missing_roles:
                role_lower = role.lower()
                if any(cs in role_lower or role_lower in cs for cs in cand_skill_names):
                    covered_missing.append(role)

            cand_unique_skills = [s for s in cand_skills_raw if str(s).lower() not in user_skill_names]

            if user_missing_roles:
                comp_ratio = len(covered_missing) / max(len(user_missing_roles), 1)
                skill_score = comp_ratio * 35.0
            else:
                skill_score = min(35.0, len(cand_unique_skills) * 5.0 + 15.0)

            # 2. Interest overlap (15%)
            user_ints = set(str(i).lower() for i in (getattr(user, 'interests', []) or []))
            cand_ints = set(str(i).lower() for i in (getattr(candidate, 'interests', []) or []))
            shared_ints_raw = user_ints & cand_ints
            shared_interests = [i for i in (getattr(candidate, 'interests', []) or []) if str(i).lower() in shared_ints_raw]
            interest_score = (len(shared_ints_raw) / max(len(user_ints | cand_ints), 1)) * 15.0

            # 3. Role fit (15%)
            user_roles = set(str(r).lower() for r in (getattr(user, 'preferred_roles', []) or []))
            cand_roles = set(str(r).lower() for r in (getattr(candidate, 'preferred_roles', []) or []))
            role_overlap = user_roles & cand_roles
            role_complement = (cand_roles - user_roles)
            role_score = min(15.0, len(role_complement) * 3.0 + len(role_overlap) * 1.5)

            # 4. Experience fit (10%)
            exp_sc = self._experience_fit(
                getattr(user, 'experience_level', 'Intermediate'),
                getattr(candidate, 'experience_level', 'Intermediate')
            ) * 10.0

            # 5. Availability (10%)
            avail_sc = self._availability_match(
                getattr(user, 'availability', 'Full-time'),
                getattr(candidate, 'availability', 'Full-time')
            ) * 10.0

            # 6. Collaboration (10%)
            collab_sc = self._collab_match(
                getattr(user, 'collaboration_preference', ''),
                getattr(candidate, 'collaboration_preference', '')
            ) * 10.0

            # 7. Mentor synergy (bonus up to 5)
            mentor_bonus = 0.0
            is_mentor_match = False
            if getattr(user, 'seeking_mentor', False) and getattr(candidate, 'is_mentor', False):
                mentor_bonus = 5.0
                is_mentor_match = True
            elif getattr(user, 'is_mentor', False) and getattr(candidate, 'seeking_mentor', False):
                mentor_bonus = 5.0
                is_mentor_match = True

            total_raw = skill_score + interest_score + role_score + exp_sc + avail_sc + collab_sc + mentor_bonus
            final_score = int(min(MAX_SCORE, max(MIN_SCORE, round(total_raw))))

            reasons = []
            if covered_missing:
                reasons.append(f"Complementary Skills: Covers {', '.join(covered_missing[:2])} which you lack for this event.")
            elif cand_unique_skills:
                reasons.append(f"Adds Unique Skills: Brings {', '.join(str(s) for s in cand_unique_skills[:2])} to expand your stack.")
            if shared_interests:
                reasons.append(f"Shared Interests: Both passionate about {', '.join(shared_interests[:2])}.")
            if avail_sc >= 7.0:
                reasons.append(f"Availability: Compatible schedule ({getattr(candidate,'availability','?')}).")
            if is_mentor_match:
                reasons.append("Mentor Synergy: Ideal beginner-mentor pairing.")
            if collab_sc >= 7.0:
                reasons.append(f"Collaboration: Aligned working culture.")
            if getattr(candidate, 'reliability_score', 0) >= 85:
                reasons.append(f"Proven Reliability: {int(candidate.reliability_score)}/100 score.")

            results.append(MatchResult(
                user_id=candidate.id,
                score=final_score,
                reasons=reasons,
                complementary_skills=covered_missing if covered_missing else [str(s) for s in cand_unique_skills[:3]],
                shared_interests=shared_interests,
                missing_skills_covered=covered_missing,
                is_mentor_match=is_mentor_match,
            ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results
