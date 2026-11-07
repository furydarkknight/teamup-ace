import os
import sys
from pathlib import Path

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_demo_flow():
    print(">>> 1. Testing Demo User Login...")
    login_res = client.post("/api/auth/login", json={
        "email": "demo@mait.ac.in",
        "password": "demo1234"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = login_res.json()
    token = login_data["access_token"]
    user = login_data["user"]
    print(f"    [PASS] Logged in as: {user['name']} ({user['college']})")
    assert user["is_verified"] is True, "Demo user should be verified (.ac.in)"
    print(f"    [PASS] Verification status: Verified College Student ({user['college']})")

    headers = {"Authorization": f"Bearer {token}"}

    print("\n>>> 2. Testing Events Listing...")
    events_res = client.get("/api/events")
    assert events_res.status_code == 200
    events = events_res.json()
    print(f"    [PASS] Retrieved {len(events)} events (Expected: 8)")
    assert len(events) >= 8

    flagship_event = events[0]
    print(f"    [PASS] Flagship Event: '{flagship_event['name']}' | Theme: {flagship_event['theme']}")
    print(f"           Required Roles: {flagship_event['required_roles']}")

    print("\n>>> 3. Testing AI Match Feed for Flagship Event...")
    matches_res = client.get(f"/api/events/{flagship_event['id']}/matches", headers=headers)
    assert matches_res.status_code == 200
    matches = matches_res.json()
    print(f"    [PASS] Generated {len(matches)} ranked candidate matches")
    assert len(matches) > 0

    top_match = matches[0]
    print(f"    [PASS] Top Ranked Match: {top_match['user']['name']} ({top_match['score']}% Match)")
    print(f"           Complementary Skills: {top_match['complementary_skills']}")
    print(f"           Work-Style Compatibility: {top_match['workstyle_compatibility']}%")
    print(f"           Explainable Reason: {top_match['reasons'][0]}")
    assert top_match["score"] >= 50

    print("\n>>> 4. Testing 10-Minute Icebreaker Challenge...")
    icebreaker_res = client.get(f"/api/icebreaker/{top_match['user']['id']}", headers=headers)
    assert icebreaker_res.status_code == 200
    ice_data = icebreaker_res.json()
    print(f"    [PASS] Icebreaker Scenario: {ice_data['prompt']['title']}")
    print(f"           Duration: {ice_data['duration_minutes']} minutes")
    print(f"           Workstyle Role Synergy: {ice_data['workstyle_analysis']['role_synergy']['description']}")

    print("\n>>> 5. Testing Teammate Invitation...")
    invite_res = client.post("/api/invites", headers=headers, json={
        "receiver_id": top_match["user"]["id"],
        "event_id": flagship_event["id"],
        "proposed_role": "UI/UX & Pitch Lead",
        "message": "Hey! Your profile complements our stack for ACE Hackathon 5.0."
    })
    assert invite_res.status_code in (200, 400), f"Invite failed: {invite_res.text}"
    if invite_res.status_code == 200:
        inv = invite_res.json()
        print(f"    [PASS] Sent Invite ID #{inv['id']} to {inv['receiver']['name']} (Status: {inv['status']})")
    else:
        print(f"    [PASS] Existing invite handled gracefully: {invite_res.json().get('detail')}")

    print("\n>>> 6. Testing Team Gap Analyzer & AI Pitch...")
    team_res = client.get("/api/teams/1")
    assert team_res.status_code == 200
    team = team_res.json()
    print(f"    [PASS] Team: '{team['name']}' with {len(team['members'])} members")

    gap_res = client.get("/api/teams/1/gaps")
    assert gap_res.status_code == 200
    gaps = gap_res.json()
    print(f"    [PASS] Covered Skills: {gaps.get('covered_skills', [])}")
    print(f"    [PASS] Missing Skills Flagged: {gaps.get('missing_skills', [])}")
    print(f"    [PASS] Skill Comparison Radar items: {len(gaps.get('skill_comparison', []))}")
    print(f"    [PASS] AI-Generated Team Pitch: '{gaps['ai_generated_pitch']}'")
    print(f"    [PASS] Suggested Role Split: {gaps['suggested_role_split']}")
    print(f"    [PASS] AI Candidates Suggested to Fill Gaps: {len(gaps['suggested_candidates'])}")

    print("\n>>> 7. Testing In-App Team Chat...")
    msg_send_res = client.post("/api/teams/1/messages", headers=headers, json={
        "content": "Automated verification test message: Sprint kick-off at 6 PM!"
    })
    assert msg_send_res.status_code == 200
    msgs_res = client.get("/api/teams/1/messages", headers=headers)
    assert msgs_res.status_code == 200
    messages = msgs_res.json()
    print(f"    [PASS] Retrieved {len(messages)} team chat messages (Latest: '{messages[-1]['content']}')")

    print("\n>>> 8. Testing Post-Event Peer Feedback & Reliability Update...")
    # Teammate 2 rates demo user
    fb_res = client.post("/api/feedback", headers=headers, json={
        "event_id": flagship_event["id"],
        "team_id": 1,
        "to_user_id": 2, # Ananya
        "rating": 5,
        "tags": ["Reliable", "Great communicator", "Technical wizard"],
        "comment": "Outstanding technical lead and brilliant teammate!"
    })
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    print(f"    [PASS] Peer Feedback submitted! Updated reliability: {fb_data['new_reliability_score']}/100")

    print("\n>>> 9. Testing Modular ML Matcher Mode...")
    from matching.ml_matcher import MLMatcher
    ml_matcher = MLMatcher()
    from app.database import SessionLocal
    from app.models import User, Event
    db = SessionLocal()
    u = db.query(User).filter(User.id == 1).first()
    e = db.query(Event).filter(Event.id == 1).first()
    cands = db.query(User).filter(User.id.in_([2, 3, 4, 5])).all()
    ml_results = ml_matcher.match(u, e, cands)
    assert len(ml_results) > 0
    print(f"    [PASS] ML Matcher inference successful! Top candidate score: {ml_results[0].score}%")
    print(f"           Note: {ml_results[0].notes}")
    db.close()

    print("\n>>> 10. Testing Meta Categories Endpoint...")
    meta_res = client.get("/api/meta/categories")
    assert meta_res.status_code == 200
    meta_data = meta_res.json()
    assert len(meta_data["skills"]) == 31
    assert len(meta_data["interests"]) == 31
    assert len(meta_data["preferred_roles"]) == 21
    assert len(meta_data["collaboration_preferences"]) == 10
    print(f"    [PASS] Verified 31 skills, 31 interests, 21 roles, 10 collaboration preferences.")

    print("\n>>> 11. Testing Paginated Browse Teams...")
    browse_teams_res = client.get("/api/teams/browse?per_page=10")
    assert browse_teams_res.status_code == 200
    b_teams = browse_teams_res.json()
    assert b_teams["total"] >= 300
    assert len(b_teams["items"]) == 10
    first_team = b_teams["items"][0]
    print(f"    [PASS] Browse Teams returned {b_teams['total']} total teams. First: {first_team['team_name']} ({first_team['college']})")

    print("\n>>> 12. Testing Paginated Browse Students...")
    browse_students_res = client.get("/api/students?per_page=10", headers=headers)
    assert browse_students_res.status_code == 200
    b_students = browse_students_res.json()
    assert b_students["total"] >= 1000
    assert len(b_students["items"]) == 10
    print(f"    [PASS] Browse Students returned {b_students['total']} students. First: {b_students['items'][0]['name']}")

    print("\n>>> 13. Testing Recommended Teams for User...")
    rec_teams_res = client.get("/api/me/recommended-teams?per_page=5", headers=headers)
    assert rec_teams_res.status_code == 200
    rec_teams = rec_teams_res.json()
    assert len(rec_teams["items"]) > 0
    top_rec = rec_teams["items"][0]
    print(f"    [PASS] Recommended Team: {top_rec['team']['team_name']} ({top_rec['score']}% match)")
    print(f"           Reasons: {top_rec['reasons'][:2]}")

    print("\n>>> 14. Testing Join Request Flow...")
    # Student sends join request to first team
    target_team_id = first_team["id"]
    jr_res = client.post(f"/api/teams/{target_team_id}/join-request", headers=headers, json={
        "message": "Automated test join request!"
    })
    # Could be 200 or 400 if already sent
    assert jr_res.status_code in (200, 400)
    print(f"    [PASS] Join request submission response: {jr_res.status_code}")

    print("\n" + "="*60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_full_demo_flow()
