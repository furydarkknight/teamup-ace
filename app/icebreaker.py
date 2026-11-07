import random
from typing import Dict, Any
from app.models import User

ICEBREAKER_PROMPTS = [
    {
        "id": "prompt-1",
        "title": "⚡ 10-Min MVP Blueprint: AI Campus Companion",
        "scenario": "Your college wants an AI-powered assistant for students to navigate course registrations, canteen queues, and campus events.",
        "task": "Collaborate to define: 1) The single killer core feature for the 24-hr MVP, 2) The frontend & backend stack, 3) Who builds what in the first 4 hours.",
        "deliverable": "A 3-bullet action plan agreed upon by both teammates."
    },
    {
        "id": "prompt-2",
        "title": "⚡ 10-Min Architecture Duel: Offline-First Health App",
        "scenario": "Rural clinics with intermittent internet need to record patient diagnostics and sync securely when back online.",
        "task": "Brainstorm: 1) What local storage/caching strategy will you use on the client? 2) How will you resolve conflict resolution during sync? 3) What is the fallback UI?",
        "deliverable": "A quick architecture flow diagram or summary in words."
    },
    {
        "id": "prompt-3",
        "title": "⚡ 10-Min Pitch Perfect Challenge",
        "scenario": "You have a 60-second elevator pitch to impress judges at the ACE International Hackathon grand finale.",
        "task": "Draft a 4-sentence pitch structure: 1) The relatable hook / painful problem, 2) The unique tech insight, 3) Demo highlight, 4) Real-world impact.",
        "deliverable": "A polished 60-second pitch script you can both recite."
    },
    {
        "id": "prompt-4",
        "title": "⚡ 10-Min Rapid UI/UX Flow",
        "scenario": "Students need a 2-tap way to find hackathon teammates based on verified college credentials.",
        "task": "Discuss: 1) What 3 pieces of information must be visible on the candidate card without clicking? 2) What is the single primary CTA? 3) How do you make the icebreaker fun?",
        "deliverable": "A 3-step user flow walkthrough."
    }
]

def calculate_workstyle_breakdown(user1: User, user2: User) -> Dict[str, Any]:
    """
    Computes a detailed work-style compatibility breakdown between two users.
    """
    # Schedule
    schedule_match = (user1.work_schedule == user2.work_schedule) or "Flexible" in (user1.work_schedule, user2.work_schedule)
    schedule_text = f"Both align on {user1.work_schedule} sprint blocks." if schedule_match else f"{user1.name} prefers {user1.work_schedule} while {user2.name} works {user2.work_schedule}."

    # Roles
    r1, r2 = user1.work_role or "", user2.work_role or ""
    if ("Leader" in r1 and "Executor" in r2) or ("Executor" in r1 and "Leader" in r2):
        role_text = "⚡ Golden Synergy: One leads the vision and timeline, while the other drives execution."
        role_score = 95
    elif "Strategist" in (r1, r2):
        role_text = "💡 Creative Balance: High strategic thinking combined with technical implementation."
        role_score = 90
    else:
        role_text = "🛠️ Peer Builder Dynamics: Dual executors capable of rapid parallel prototyping."
        role_score = 85

    # Vibe
    v1, v2 = user1.work_vibe or "Balanced", user2.work_vibe or "Balanced"
    vibe_match = (v1 == v2) or ("Balanced" in (v1, v2))
    vibe_text = f"Shared team culture: {v1} & {v2} mindset." if vibe_match else "Diverse working rhythms."

    overall_compat = int((role_score + (90 if schedule_match else 70) + (90 if vibe_match else 70)) / 3)

    return {
        "overall_compatibility": overall_compat,
        "schedule": {"status": "High" if schedule_match else "Medium", "description": schedule_text},
        "role_synergy": {"score": role_score, "description": role_text},
        "vibe": {"status": "Aligned" if vibe_match else "Complementary", "description": vibe_text}
    }

def get_icebreaker_challenge(user1: User, user2: User) -> Dict[str, Any]:
    """
    Picks an icebreaker challenge and attaches work-style compatibility analysis.
    """
    prompt = ICEBREAKER_PROMPTS[(user1.id + user2.id) % len(ICEBREAKER_PROMPTS)]
    workstyle = calculate_workstyle_breakdown(user1, user2)

    return {
        "prompt": prompt,
        "duration_minutes": 10,
        "workstyle_analysis": workstyle,
        "partner": {
            "id": user2.id,
            "name": user2.name,
            "college": user2.college,
            "avatar_url": user2.avatar_url,
            "skills": user2.skills,
            "reliability_score": user2.reliability_score
        }
    }
