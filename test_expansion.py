"""
Automated End-to-End Test Suite for ACE TeamUp Platform Expansion (Phases 1 - 8)
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from app.main import app

client = TestClient(app)

def test_expansion_suite():
    print("\n" + "="*70)
    print(">>> RUNNING PLATFORM EXPANSION END-TO-END VERIFICATION SUITE")
    print("="*70 + "\n")

    # 1. Login as Demo Student (Aarav Sharma)
    print(">>> 1. Authenticating as Demo Student (Aarav Sharma)...")
    res = client.post("/api/auth/login", json={"email": "demo@mait.ac.in", "password": "demo1234"})
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {token}"}
    print("    [PASS] Student authenticated successfully.")

    # 2. Opportunities Hub (Phase 1)
    print(">>> 2. Testing Opportunities Hub (Phase 1)...")
    res = client.get("/api/opportunities")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 60, f"Expected at least 60 opportunities, got {data['total']}"
    opp_id = data["items"][0]["id"]
    print(f"    [PASS] Retrieved {data['total']} opportunities across 16 categories.")

    res = client.get(f"/api/opportunities/{opp_id}", headers=student_headers)
    assert res.status_code == 200
    opp_detail = res.json()
    assert "title" in opp_detail and "rounds" in opp_detail
    print(f"    [PASS] Opportunity detail retrieved: '{opp_detail['title']}' | Type: {opp_detail['type']}")

    # Register for opportunity
    res = client.post(f"/api/opportunities/{opp_id}/register", headers=student_headers)
    assert res.status_code == 200
    print("    [PASS] Registered for opportunity successfully.")

    # 3. Jobs & Internships Portal (Phase 2)
    print(">>> 3. Testing Jobs & Internships Portal (Phase 2)...")
    res = client.get("/api/jobs")
    assert res.status_code == 200
    jobs_data = res.json()
    assert jobs_data["total"] >= 40
    job_id = jobs_data["items"][0]["id"]
    print(f"    [PASS] Retrieved {jobs_data['total']} jobs/internships.")

    res = client.get("/api/jobs/recommendations", headers=student_headers)
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) > 0
    print(f"    [PASS] Skill-based job recommendation generated! Top match: {recs[0]['job']['title']} ({recs[0]['match_score']}%)")

    # One-click apply
    res = client.post(f"/api/jobs/{job_id}/apply", json={"cover_note": "Excited for this role!"}, headers=student_headers)
    assert res.status_code == 200
    print("    [PASS] One-click apply executed successfully.")

    # 4. Resume Builder (Phase 2)
    print(">>> 4. Testing Resume Builder...")
    res = client.get("/api/resumes", headers=student_headers)
    assert res.status_code == 200
    resumes = res.json()
    assert len(resumes) >= 1
    print(f"    [PASS] Retrieved {len(resumes)} resume(s) for demo student (Default: '{resumes[0]['title']}').")

    # 5. My Space: Applications Tracker (Phase 3)
    print(">>> 5. Testing Applications Tracking & Timeline (Phase 3)...")
    res = client.get("/api/applications/my", headers=student_headers)
    assert res.status_code == 200
    app_data = res.json()
    assert len(app_data["items"]) >= 1
    print(f"    [PASS] Retrieved {len(app_data['items'])} tracked applications | Profile Completeness: {app_data['profile_completeness']}%")

    # 6. Learn: Courses, Quizzes & Assessments (Phase 4)
    print(">>> 6. Testing Learn: Courses & Skill Assessments (Phase 4)...")
    res = client.get("/api/learn/courses")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 40
    c_id = data["items"][0]["id"]
    print(f"    [PASS] Catalog retrieved {data['total']} courses across SKILLS list.")

    res = client.get("/api/learn/paths")
    assert res.status_code == 200
    paths = res.json()
    assert len(paths) >= 6
    print(f"    [PASS] Retrieved {len(paths)} career learning paths (e.g. '{paths[0]['title']}').")

    res = client.get("/api/learn/assessments")
    assert res.status_code == 200
    assessments = res.json()
    assert len(assessments) >= 20
    ass_id = assessments[0]["id"]
    print(f"    [PASS] Retrieved {len(assessments)} skill assessments (e.g. '{assessments[0]['title']}').")

    # Submit assessment with correct answers (passing)
    res = client.post(f"/api/learn/assessments/{ass_id}/submit", json={"answers": [0, 0, 0]}, headers=student_headers)
    assert res.status_code == 200
    ass_result = res.json()
    assert ass_result["passed"] == True
    print(f"    [PASS] Passed assessment: {ass_result['score']}%! Issued cert: {ass_result['issued_certificate_id']}")

    # Test Learn-to-Qualify
    res = client.get("/api/learn/learn-to-qualify?team_id=1", headers=student_headers)
    assert res.status_code == 200
    print("    [PASS] Learn-to-qualify engine evaluated team skill gaps.")

    # 7. Certificates & Public Verification (Phase 5)
    print(">>> 7. Testing Certificates & Public Verification (Phase 5)...")
    res = client.get("/api/certificates/my", headers=student_headers)
    assert res.status_code == 200
    my_certs = res.json()
    assert len(my_certs) >= 1
    sample_uid = my_certs[0]["unique_id"]
    print(f"    [PASS] Retrieved {len(my_certs)} certificate(s) for demo student.")

    # Public verification
    res = client.get(f"/api/certificates/verify/{sample_uid}")
    assert res.status_code == 200
    cert_verify = res.json()
    assert cert_verify["valid"] == True
    print(f"    [PASS] Public verification validated certificate: '{cert_verify['title']}' for {cert_verify['recipient_name']}.")

    # 8. Digital Portfolio (Phase 5)
    print(">>> 8. Testing Public Digital Portfolio (/u/{username})...")
    res = client.get("/api/portfolio/u/aaravsharma")
    assert res.status_code == 200
    portfolio = res.json()
    assert portfolio["name"] == "Aarav Sharma"
    assert len(portfolio["skills"]) > 0
    print(f"    [PASS] Digital portfolio loaded for @aaravsharma with {len(portfolio['skills'])} skills & {len(portfolio['certificates'])} certs.")

    # 9. Community: Mentors, Alumni & Forums (Phase 6)
    print(">>> 9. Testing Community, Mentors & Forums (Phase 6)...")
    res = client.get("/api/community/mentors")
    assert res.status_code == 200
    mentors = res.json()
    assert len(mentors) >= 20
    print(f"    [PASS] Retrieved {len(mentors)} mentors.")

    res = client.get("/api/community/alumni")
    assert res.status_code == 200
    alumni = res.json()
    assert len(alumni) >= 30
    print(f"    [PASS] Retrieved {len(alumni)} alumni.")

    res = client.get("/api/community/colleges")
    assert res.status_code == 200
    colleges = res.json()
    assert len(colleges) >= 10
    print(f"    [PASS] Retrieved {len(colleges)} colleges with student clubs.")

    # 10. Role Portals (Phase 7)
    print(">>> 10. Testing Role Portals (Organizer, Recruiter, Admin)...")
    # Recruiter login
    res = client.post("/api/auth/login", json={"email": "recruiter@nexuslabs.com", "password": "demo1234"})
    assert res.status_code == 200
    rec_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}

    res = client.get("/api/portals/recruiter/talent-search?skill=Python&verified_only=true", headers=rec_headers)
    assert res.status_code == 200
    talent = res.json()
    assert talent["total"] > 0
    print(f"    [PASS] Recruiter talent search retrieved {talent['total']} verified students across universities.")

    # Admin login
    res = client.post("/api/auth/login", json={"email": "admin@allcollegeevent.com", "password": "admin1234"})
    assert res.status_code == 200
    admin_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    res = client.get("/api/portals/admin/dashboard", headers=admin_headers)
    assert res.status_code == 200
    admin_data = res.json()
    print(f"    [PASS] Admin overview loaded: {admin_data['metrics']['total_users']} users, {admin_data['metrics']['opportunities']} opportunities.")

    # 11. Unified Global Search
    print(">>> 11. Testing Unified Global Search...")
    res = client.get("/api/search?q=Python")
    assert res.status_code == 200
    search_res = res.json()["results"]
    print(f"    [PASS] Global search for 'Python' returned: {len(search_res['courses'])} courses, {len(search_res['jobs'])} jobs, {len(search_res['opportunities'])} opportunities.")

    # 12. Notification Center
    print(">>> 12. Testing Notification Center...")
    res = client.get("/api/notifications", headers=student_headers)
    assert res.status_code == 200
    notifs = res.json()
    print(f"    [PASS] Retrieved {len(notifs['items'])} notifications ({notifs['unread_count']} unread).")

    # 13. Advanced TeamUp Features (Phase 8)
    print(">>> 13. Testing Advanced TeamUp Features (Phase 8)...")
    # What If I Join Simulator
    res = client.get("/api/teams/1/what-if", headers=student_headers)
    assert res.status_code == 200
    what_if = res.json()
    print(f"    [PASS] 'What if I join?' simulator computed: Coverage before={what_if['before']['coverage_percent']}%, after={what_if['after']['coverage_percent']}% (+{what_if['coverage_boost']}%)")

    # Skill Heatmap
    res = client.get("/api/teams/1/skill-heatmap")
    assert res.status_code == 200
    heatmap = res.json()
    print(f"    [PASS] Team skill heatmap generated: {heatmap['covered_count']} covered, {heatmap['missing_count']} missing.")

    # Team Balance Score
    res = client.get("/api/teams/1/balance-score")
    assert res.status_code == 200
    bal = res.json()
    print(f"    [PASS] Team balance score: {bal['balance_score']}/100 | Status: {bal['health_status']}")

    # Kanban tasks
    res = client.get("/api/teams/1/tasks")
    assert res.status_code == 200
    tasks = res.json()
    print(f"    [PASS] Team room kanban checklist loaded with {len(tasks)} tasks.")

    # 14. Testing Interactive Action Modals & Workflows
    print(">>> 14. Testing Interactive Action Modals & Workflows (Mentorship, Referrals, Forum, Alerts, Portals)...")
    # Mentor booking
    b_res = client.post("/api/community/mentors/book", headers=student_headers, json={
        "mentor_id": 1, "scheduled_at": "Saturday 11:00 AM", "topic": "Architecture and Pitch Review"
    })
    assert b_res.status_code == 200
    print("    [PASS] Mentor 1:1 session booked successfully.")

    # Alumni referral request
    r_res = client.post("/api/community/alumni/referral-request", headers=student_headers, json={
        "alumni_id": 1, "job_url": "https://company.com/jobs/sde1", "resume_link": "https://drive.google.com/resume.pdf", "note": "Targeting SDE 1"
    })
    assert r_res.status_code == 200
    print("    [PASS] Alumni referral request dispatched.")

    # Community forum discussion post
    f_res = client.post("/api/community/forum/threads", headers=student_headers, json={
        "title": "Scaling FastAPI WebSockets with Redis", "content": "Production tips for 10k connections?", "skill_name": "Python"
    })
    assert f_res.status_code == 200
    print("    [PASS] Technical forum thread posted.")

    # Job Alert
    a_res = client.post("/api/jobs/alerts", headers=student_headers, json={
        "keyword": "FastAPI", "role": "Backend Developer", "location": "Remote", "min_stipend": "30,000/mo"
    })
    assert a_res.status_code == 200
    print("    [PASS] Job alert configured and active.")

    # Organizer opportunity creation
    org_res = client.post("/api/auth/login", json={"email": "organizer@delhitechexpo.edu", "password": "demo1234"})
    assert org_res.status_code == 200
    org_headers = {"Authorization": f"Bearer {org_res.json()['access_token']}"}

    opp_res = client.post("/api/portals/organizer/opportunities", headers=org_headers, json={
        "title": "Delhi AI Innovation Sprint 2026", "type": "Hackathon", "description": "48 hour innovation sprint",
        "skills": ["Python", "FastAPI"], "location_mode": "Online", "deadline": "In 21 days", "prize_pool": "3,00,000",
        "team_size_min": 2, "team_size_max": 4
    })
    assert opp_res.status_code == 200
    print(f"    [PASS] Organizer published opportunity live (ID {opp_res.json().get('id')}).")

    # Recruiter application status update
    status_res = client.put("/api/portals/recruiter/applications/1/status", headers=rec_headers, json={
        "status": "Shortlisted", "note": "Strong match on skills and experience."
    })
    assert status_res.status_code == 200
    print("    [PASS] Recruiter updated candidate status.")

    # Notification mark all read
    n_res = client.post("/api/notifications/mark-all-read", headers=student_headers)
    assert n_res.status_code == 200
    print("    [PASS] Notifications marked read.")

    print("\n" + "="*70)
    print(">>> ALL EXPANSION SUITE TESTS PASSED WITH 100% SUCCESS!")
    print("="*70 + "\n")

if __name__ == "__main__":
    test_expansion_suite()
