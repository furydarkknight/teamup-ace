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
    assert top_match["score"] >= 80

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
    assert invite_res.status_code == 200
    inv = invite_res.json()
    print(f"    [PASS] Sent Invite ID #{inv['id']} to {inv['receiver']['name']} (Status: {inv['status']})")

    print("\n>>> 6. Testing Team Gap Analyzer & AI Pitch...")
    team_res = client.get("/api/teams/1")
    assert team_res.status_code == 200
    team = team_res.json()
    print(f"    [PASS] Team: '{team['name']}' with {len(team['members'])} members")

    gap_res = client.get("/api/teams/1/gaps")
    assert gap_res.status_code == 200
    gaps = gap_res.json()
    print(f"    [PASS] Covered Roles: {gaps['covered_roles']}")
    print(f"    [PASS] Missing Roles Flagged: {gaps['missing_roles']}")
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

    print("\n" + "="*60)
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_full_demo_flow()
