from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Team, Event, User, TeamMember
from matching import get_matcher

def generate_ai_team_pitch(team_name: str, event_theme: str, covered_roles: List[str], members_count: int) -> str:
    """
    Template-based AI hook generator tailored to the team's skillset and event theme.
    """
    roles_str = " & ".join(covered_roles[:2]) if covered_roles else "Full-Stack Innovation"
    
    pitches = [
        f"A high-velocity {roles_str} squad primed to engineer breakthrough solutions for {event_theme}.",
        f"Fusing deep expertise in {roles_str} with relentless execution to take top podium at the hackathon.",
        f"Cross-functional builders uniting {roles_str} to transform ideas into a production-grade {event_theme} MVP.",
        f"Agile builders combining strategic domain knowledge with technical execution in {roles_str}."
    ]
    # Deterministic choice based on team name hash
    idx = sum(ord(c) for c in team_name) % len(pitches)
    return pitches[idx]

def generate_suggested_role_split(team: Team, event: Event) -> Dict[str, str]:
    """
    Suggests an optimal division of labor across current team members based on their declared skills.
    """
    role_split = {}
    event_roles = list(event.required_roles) if event else []

    assigned_roles = set()

    for idx, member in enumerate(team.members):
        user = member.user
        member_skills = [s.get("name", "") for s in user.skills]
        
        # Match member skills to event roles
        best_role = None
        for er in event_roles:
            if er not in assigned_roles:
                for ms in member_skills:
                    if ms.lower() in er.lower() or er.lower() in ms.lower():
                        best_role = er
                        break
            if best_role:
                break
        
        if not best_role:
            best_role = member.role or (f"Technical Lead & Architecture" if idx == 0 else f"Core Builder ({', '.join(member_skills[:1])})")

        assigned_roles.add(best_role)
        role_split[user.name] = best_role

    return role_split

def analyze_team_gaps(team: Team, event: Event, db: Session) -> Dict[str, Any]:
    """
    Compares team skills against event's required roles,
    flags missing skills, and suggests top candidates for each missing role.
    """
    required_roles = list(event.required_roles) if event else []
    
    # Collect all skills in current team
    team_skills_names = set()
    team_user_ids = {m.user_id for m in team.members}

    for member in team.members:
        for s in member.user.skills:
            team_skills_names.add(s.get("name", "").strip().lower())

    covered_roles = []
    missing_roles = []

    for role in required_roles:
        r_lower = role.lower()
        if any(ts in r_lower or r_lower in ts for ts in team_skills_names):
            covered_roles.append(role)
        else:
            missing_roles.append(role)

    # Suggest candidates for missing roles
    suggested_candidates = []
    if missing_roles:
        all_candidates = db.query(User).filter(~User.id.in_(team_user_ids)).limit(30).all()
        matcher = get_matcher()
        matched = matcher.match(team.leader, event, all_candidates)

        # For each missing role, find top matching candidate who has this role
        seen_cand_ids = set()
        for missing_role in missing_roles:
            m_lower = missing_role.lower()
            role_cand_found = False

            for match_res in matched:
                cand_id = match_res.user_id
                if cand_id in seen_cand_ids:
                    continue
                cand_user = next((c for c in all_candidates if c.id == cand_id), None)
                if not cand_user:
                    continue

                has_skill = any(m_lower in s.get("name", "").lower() or s.get("name", "").lower() in m_lower for s in cand_user.skills)
                if has_skill:
                    suggested_candidates.append({
                        "role": missing_role,
                        "user": cand_user,
                        "score": match_res.score,
                        "reason": f"Covers missing role '{missing_role}' with high proficiency."
                    })
                    seen_cand_ids.add(cand_id)
                    role_cand_found = True
                    break

            # Fallback if no specific role holder among top, take top match
            if not role_cand_found and matched:
                for match_res in matched:
                    if match_res.user_id not in seen_cand_ids:
                        cand_user = next((c for c in all_candidates if c.id == match_res.user_id), None)
                        if cand_user:
                            suggested_candidates.append({
                                "role": missing_role,
                                "user": cand_user,
                                "score": match_res.score,
                                "reason": f"Top compatible candidate ({match_res.score}% match) to bridge '{missing_role}'."
                            })
                            seen_cand_ids.add(cand_user.id)
                            break

    role_split = generate_suggested_role_split(team, event)
    team_pitch = generate_ai_team_pitch(team.name, event.theme, covered_roles, len(team.members))

    return {
        "team_id": team.id,
        "event_id": event.id,
        "required_roles": required_roles,
        "covered_roles": covered_roles,
        "missing_roles": missing_roles,
        "suggested_role_split": role_split,
        "ai_generated_pitch": team.pitch or team_pitch,
        "suggested_candidates": suggested_candidates
    }
