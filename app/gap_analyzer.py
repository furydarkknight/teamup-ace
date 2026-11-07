from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Team, Event, User, TeamMember
from matching import get_matcher

def generate_ai_team_pitch(team_name: str, theme: str, covered_skills: List[str], members_count: int) -> str:
    roles_str = " & ".join(covered_skills[:2]) if covered_skills else "Full-Stack Innovation"
    pitches = [
        f"A high-velocity {roles_str} squad primed to engineer breakthrough solutions for {theme}.",
        f"Fusing deep expertise in {roles_str} with relentless execution to take top podium.",
        f"Cross-functional builders uniting {roles_str} to deliver a production-grade MVP.",
        f"Agile builders combining strategic domain knowledge with technical execution in {roles_str}.",
    ]
    idx = sum(ord(c) for c in team_name) % len(pitches)
    return pitches[idx]

def generate_suggested_role_split(team: Team) -> Dict[str, str]:
    role_split = {}
    preferred_roles = team.preferred_roles or []
    assigned_roles = set()
    for idx, member in enumerate(team.members or []):
        user = member.user
        if not user:
            continue
        member_skills = user.skills or []
        best_role = None
        for pr in preferred_roles:
            if pr not in assigned_roles:
                for ms in member_skills:
                    if ms.lower() in pr.lower() or pr.lower() in ms.lower():
                        best_role = pr
                        break
            if best_role:
                break
        if not best_role:
            if idx == 0:
                best_role = "Technical Lead & Architecture"
            else:
                best_role = f"Core Builder ({', '.join(member_skills[:1])})" if member_skills else "Team Member"
        assigned_roles.add(best_role)
        role_split[user.name] = best_role
    return role_split

def analyze_team_gaps(team: Team, event, db: Session) -> Dict[str, Any]:
    """
    Compares team's current_skills vs required_skills/skill_requirements.
    Returns skill_comparison list for bar chart + suggested candidates.
    """
    required_list = team.required_skills or []
    skill_reqs = team.skill_requirements or {}  # {skill: min_level}
    current_skills = team.current_skills or {}  # {skill: current_level}

    all_required = set(required_list)
    for s in skill_reqs:
        all_required.add(s)

    skill_comparison = []
    missing_skills = []
    covered_skills = []

    for skill in sorted(all_required):
        required_level = skill_reqs.get(skill, 1)
        current_level = current_skills.get(skill, 0)
        gap = max(0, required_level - current_level)
        is_covered = current_level >= required_level
        skill_comparison.append({
            "skill": skill,
            "required_level": required_level,
            "current_level": current_level,
            "gap": gap,
            "covered": is_covered
        })
        if is_covered:
            covered_skills.append(skill)
        else:
            missing_skills.append(skill)

    suggested_candidates = []
    team_member_ids = {m.user_id for m in (team.members or [])}

    if missing_skills:
        all_candidates = db.query(User).filter(
            ~User.id.in_(team_member_ids)
        ).limit(50).all()

        matcher = get_matcher()
        matched = matcher.match_team_to_students(team, all_candidates)

        seen = set()
        student_lookup = {s.id: s for s in all_candidates}

        for missing_skill in missing_skills[:5]:
            for match_res in matched:
                if match_res.user_id in seen:
                    continue
                cand = student_lookup.get(match_res.user_id)
                if not cand:
                    continue
                has_skill = missing_skill.lower() in [str(s).lower() for s in (cand.skills or [])]
                if has_skill:
                    suggested_candidates.append({
                        "role": missing_skill,
                        "user": cand,
                        "score": match_res.score,
                        "reason": f"Covers missing '{missing_skill}' - {match_res.score}% team match."
                    })
                    seen.add(match_res.user_id)
                    break

    theme = event.theme if event else "Hackathon Innovation"
    role_split = generate_suggested_role_split(team)
    pitch = generate_ai_team_pitch(
        team.team_name or team.name, theme, covered_skills, len(team.members or [])
    )

    return {
        "team_id": team.id,
        "event_id": event.id if event else None,
        "required_skills": list(all_required),
        "skill_requirements": skill_reqs,
        "current_skills": current_skills,
        "missing_skills": missing_skills,
        "covered_skills": covered_skills,
        "skill_comparison": skill_comparison,
        "suggested_role_split": role_split,
        "ai_generated_pitch": team.pitch or pitch,
        "suggested_candidates": suggested_candidates,
    }
