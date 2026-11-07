from typing import List, Dict, Any, Tuple
from app.config import WORK_STYLES
from matching.base import BaseMatcher, MatchResult

class RuleBasedMatcher(BaseMatcher):
    """
    Default rule-based matching engine with weighted scoring:
    - 40% Complementary skills (reward covering skills user lacks for the event)
    - 20% Availability overlap
    - 15% Experience-level fit & Mentor synergy
    - 15% Goal alignment
    - 10% Work-style compatibility
    """

    def match(self, user: Any, event: Any, candidates: List[Any]) -> List[MatchResult]:
        results: List[MatchResult] = []

        if not candidates:
            return results

        user_skill_names = {s.get("name", "").strip().lower() for s in user.skills}
        event_required_roles = [r.strip() for r in (event.required_roles if event else [])]

        # Calculate what the user is missing for this event
        user_missing_event_roles = []
        for role in event_required_roles:
            role_lower = role.lower()
            if not any(us in role_lower or role_lower in us for us in user_skill_names):
                user_missing_event_roles.append(role)

        for candidate in candidates:
            # Skip candidate if they blocked user or user blocked them
            if candidate.id == user.id:
                continue
            if candidate.id in (user.blocked_users or []):
                continue
            if user.id in (candidate.blocked_users or []):
                continue

            cand_skill_names = {s.get("name", "").strip().lower() for s in candidate.skills}
            cand_skill_display = [s.get("name", "") for s in candidate.skills]

            # 1. COMPLEMENTARY SKILLS (40%)
            # Does candidate cover the roles this user lacks for the event?
            covered_missing = []
            for role in user_missing_event_roles:
                role_lower = role.lower()
                if any(cs in role_lower or role_lower in cs for cs in cand_skill_names):
                    covered_missing.append(role)

            # Complementary tech skills
            cand_unique_skills = []
            for cs in candidate.skills:
                cname = cs.get("name", "")
                if cname.lower() not in user_skill_names:
                    cand_unique_skills.append(cname)

            if user_missing_event_roles:
                complement_ratio = len(covered_missing) / max(len(user_missing_event_roles), 1)
                skill_score = min(40.0, complement_ratio * 35.0 + (5.0 if cand_unique_skills else 0.0))
            else:
                # If user already covers everything, reward unique skills candidate brings
                complement_ratio = min(1.0, len(cand_unique_skills) / 3.0) if cand_unique_skills else 0.5
                skill_score = 25.0 + (complement_ratio * 15.0)

            # 2. AVAILABILITY OVERLAP (20%)
            user_avail = (user.availability or "").lower()
            cand_avail = (candidate.availability or "").lower()
            if "flexible" in user_avail or "flexible" in cand_avail:
                avail_score = 20.0
                avail_match_type = "Flexible availability overlap"
            elif user_avail == cand_avail:
                avail_score = 20.0
                avail_match_type = f"Both available on {user.availability}"
            elif ("weekend" in user_avail and "evening" in cand_avail) or ("evening" in user_avail and "weekend" in cand_avail):
                avail_score = 14.0
                avail_match_type = f"Compatible schedules ({user.availability} & {candidate.availability})"
            else:
                avail_score = 8.0
                avail_match_type = f"Partial availability ({user.availability} vs {candidate.availability})"

            # 3. EXPERIENCE & MENTOR FIT (15%)
            exp_score = 10.0
            is_mentor_match = False
            user_exp = (user.experience_level or "Intermediate").lower()
            cand_exp = (candidate.experience_level or "Intermediate").lower()

            # Mentor synergy check
            if user.seeking_mentor and candidate.is_mentor:
                exp_score = 15.0
                is_mentor_match = True
            elif user.is_mentor and candidate.seeking_mentor:
                exp_score = 15.0
                is_mentor_match = True
            elif user_exp == cand_exp:
                exp_score = 14.0
            elif (user_exp == "advanced" and cand_exp == "intermediate") or (user_exp == "intermediate" and cand_exp == "advanced"):
                exp_score = 13.0
            else:
                exp_score = 9.0

            # 4. GOAL ALIGNMENT (15%)
            user_goal = user.goal or "Win Grand Prize"
            cand_goal = candidate.goal or "Win Grand Prize"
            if user_goal.lower() == cand_goal.lower():
                goal_score = 15.0
                goal_text = f"Both aim to '{user_goal}'"
            elif ("win" in user_goal.lower() and "learn" in cand_goal.lower()) or ("learn" in user_goal.lower() and "win" in cand_goal.lower()):
                goal_score = 11.0
                goal_text = f"Complementary drive ({user_goal} & {cand_goal})"
            else:
                goal_score = 8.0
                goal_text = f"Diverse perspectives ({user_goal} vs {cand_goal})"

            # 5. WORK-STYLE COMPATIBILITY (10%)
            # Schedule compatibility
            ws_score = 0.0
            if user.work_schedule == candidate.work_schedule or "Flexible" in (user.work_schedule, candidate.work_schedule):
                ws_score += 3.5
            else:
                ws_score += 1.5

            # Role synergy: Leader + Executor is better than Leader + Leader
            user_wr = user.work_role or "Executor / Builder"
            cand_wr = candidate.work_role or "Executor / Builder"
            if ("Leader" in user_wr and "Executor" in cand_wr) or ("Executor" in user_wr and "Leader" in cand_wr):
                ws_score += 4.0
                role_synergy = "Ideal leadership & execution balance (Leader + Executor)"
            elif "Strategist" in user_wr or "Strategist" in cand_wr:
                ws_score += 3.5
                role_synergy = "Creative balance with strategic ideation"
            elif user_wr == cand_wr and "Leader" in user_wr:
                ws_score += 2.0
                role_synergy = "Both have strong leadership instincts"
            else:
                ws_score += 3.0
                role_synergy = "Collaborative builders mindset"

            # Vibe
            if user.work_vibe == candidate.work_vibe or "Balanced" in (user.work_vibe, candidate.work_vibe):
                ws_score += 2.5
            else:
                ws_score += 1.0

            # Shared interests
            user_interests = set(user.interests or [])
            cand_interests = set(candidate.interests or [])
            shared_interests = list(user_interests.intersection(cand_interests))

            # Total score calculation
            total_raw = skill_score + avail_score + exp_score + goal_score + ws_score
            final_score = int(min(99, max(50, round(total_raw))))

            # Calculate workstyle percentage
            workstyle_pct = int(min(98, max(55, round((ws_score / 10.0) * 100))))

            # Formulate explainable reasons
            reasons = []
            if covered_missing:
                reasons.append(f"🎯 Complementary Roles: Covers {', '.join(covered_missing[:2])} which your profile lacks for this event.")
            elif cand_unique_skills:
                reasons.append(f"🛠️ Adds Unique Skills: Brings {', '.join(cand_unique_skills[:2])} to expand your stack.")

            if is_mentor_match:
                reasons.append("🎓 Mentor Synergy: Ideal beginner-mentor pairing to guide technical execution.")

            if avail_score >= 18.0:
                reasons.append(f"⏰ High Schedule Match: {avail_match_type}.")

            if goal_score >= 14.0:
                reasons.append(f"🏆 Goal Aligned: {goal_text}.")

            reasons.append(f"🤝 Work Style Fit ({workstyle_pct}%): {role_synergy}.")

            if shared_interests:
                reasons.append(f"💡 Shared Domains: Passionate about {', '.join(shared_interests[:2])}.")

            if candidate.reliability_score and candidate.reliability_score >= 85:
                reasons.append(f"⭐ Proven Reliability: High reliability track record ({int(candidate.reliability_score)}/100).")

            results.append(MatchResult(
                user_id=candidate.id,
                score=final_score,
                reasons=reasons,
                complementary_skills=covered_missing if covered_missing else cand_unique_skills[:3],
                shared_interests=shared_interests,
                workstyle_compatibility=workstyle_pct,
                is_mentor_match=is_mentor_match,
                notes=None
            ))

        # Sort descending by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results
