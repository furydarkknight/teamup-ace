"""
Learn: Courses, Assessments & Skill Building API Routes (Phase 4)
Course catalog, module quizzes, skill assessments with verified badges, learning paths,
and the unique "Learn-to-Qualify" skill gap closer.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
import json
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user_optional, get_current_user
from app.models import User, Team
from app.models_expansion import (
    Course, CourseModule, CourseLesson, CourseEnrollment,
    LessonProgress, Assessment, AssessmentAttempt, LearningPath,
    Certificate, VerifiedSkill
)

router = APIRouter(prefix="/api/learn", tags=["Learn: Courses & Assessments"])


class AssessmentSubmitRequest(BaseModel):
    answers: List[int] # List of chosen option indices


@router.get("/courses")
def list_courses(
    skill: Optional[str] = None,
    level: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db)
):
    query = db.query(Course)

    if skill and skill != "All":
        query = query.filter(Course.skill_tags_json.ilike(f"%{skill}%"))

    if level and level != "All":
        query = query.filter(Course.level == level)

    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            or_(
                Course.title.ilike(s),
                Course.description.ilike(s),
                Course.skill_tags_json.ilike(s)
            )
        )

    total = query.count()
    items = query.order_by(desc(Course.enrolled_count)).offset((page - 1) * limit).limit(limit).all()

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": (total + limit - 1) // limit,
        "items": [
            {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "skill_tags": c.skill_tags,
                "level": c.level,
                "duration": c.duration,
                "is_free": c.is_free,
                "mock_price": c.mock_price,
                "instructor_name": c.instructor_name,
                "rating": c.rating,
                "enrolled_count": c.enrolled_count,
                "thumbnail_url": c.thumbnail_url
            }
            for c in items
        ]
    }


@router.get("/courses/{id}")
def get_course_detail(
    id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    is_enrolled = False
    progress = 0.0
    if current_user:
        enr = db.query(CourseEnrollment).filter(
            CourseEnrollment.user_id == current_user.id,
            CourseEnrollment.course_id == course.id
        ).first()
        if enr:
            is_enrolled = True
            progress = enr.progress_percent

    modules_data = []
    for mod in course.modules:
        modules_data.append({
            "id": mod.id,
            "title": mod.title,
            "order_num": mod.order_num,
            "lessons": [
                {
                    "id": l.id,
                    "title": l.title,
                    "order_num": l.order_num,
                    "content_type": l.content_type,
                    "content": l.content,
                    "quiz_data": l.quiz_data
                }
                for l in mod.lessons
            ]
        })

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "skill_tags": course.skill_tags,
        "level": course.level,
        "duration": course.duration,
        "instructor_name": course.instructor_name,
        "instructor_title": course.instructor_title,
        "rating": course.rating,
        "enrolled_count": course.enrolled_count,
        "thumbnail_url": course.thumbnail_url,
        "is_enrolled": is_enrolled,
        "progress": progress,
        "modules": modules_data
    }


@router.post("/courses/{id}/enroll")
def enroll_in_course(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == current_user.id,
        CourseEnrollment.course_id == course.id
    ).first()
    if existing:
        return {"message": "Already enrolled", "enrollment_id": existing.id, "progress": existing.progress_percent}

    enr = CourseEnrollment(
        user_id=current_user.id,
        course_id=course.id,
        progress_percent=0.0
    )
    db.add(enr)
    course.enrolled_count = (course.enrolled_count or 0) + 1
    db.commit()

    return {"message": f"Enrolled in {course.title}!", "enrollment_id": enr.id}


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    lesson = db.query(CourseLesson).filter(CourseLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    course = lesson.module.course
    enr = db.query(CourseEnrollment).filter(
        CourseEnrollment.user_id == current_user.id,
        CourseEnrollment.course_id == course.id
    ).first()
    if not enr:
        enr = CourseEnrollment(user_id=current_user.id, course_id=course.id, progress_percent=0.0)
        db.add(enr)
        db.flush()

    # Track progress
    existing_lp = db.query(LessonProgress).filter(
        LessonProgress.enrollment_id == enr.id,
        LessonProgress.lesson_id == lesson.id
    ).first()
    if not existing_lp:
        lp = LessonProgress(enrollment_id=enr.id, lesson_id=lesson.id, is_completed=True)
        db.add(lp)
        db.flush()

    # Calculate overall progress
    total_lessons = sum(len(m.lessons) for m in course.modules)
    completed_lessons = db.query(LessonProgress).filter(LessonProgress.enrollment_id == enr.id).count()
    enr.progress_percent = min(100.0, round((completed_lessons / max(1, total_lessons)) * 100, 1))

    # If 100% complete, issue certificate automatically
    issued_cert = None
    if enr.progress_percent >= 100.0 and not enr.is_completed:
        enr.is_completed = True
        enr.completed_at = datetime.utcnow()
        uid = f"ACE-CERT-{datetime.utcnow().year}-{current_user.id:04d}{course.id:02d}-{datetime.utcnow().strftime('%H%M%S%f')[:10]}"
        cert = Certificate(
            unique_id=uid,
            user_id=current_user.id,
            recipient_name=current_user.name,
            title=f"Course Completion: {course.title}",
            issuer="AllCollegeEvent.com (ACE) Academy",
            certificate_type="course",
            item_id=course.id,
            qr_code_data=f"https://allcollegeevent.com/verify/{uid}",
            metadata_json=json.dumps({"course": course.title, "score": "100%", "verified": True})
        )
        db.add(cert)
        issued_cert = uid

    db.commit()
    return {
        "message": "Lesson marked as complete!",
        "progress": enr.progress_percent,
        "is_completed": enr.is_completed,
        "issued_certificate_id": issued_cert
    }


@router.get("/paths")
def list_learning_paths(db: Session = Depends(get_db)):
    paths = db.query(LearningPath).all()
    results = []
    for p in paths:
        course_objects = db.query(Course).filter(Course.id.in_(p.course_ids)).all()
        results.append({
            "id": p.id,
            "title": p.title,
            "role_target": p.role_target,
            "description": p.description,
            "badge_icon": p.badge_icon,
            "capstone_project": p.capstone_project,
            "courses_count": len(course_objects),
            "courses": [
                {
                    "id": c.id,
                    "title": c.title,
                    "level": c.level,
                    "duration": c.duration
                }
                for c in course_objects
            ]
        })
    return results


@router.get("/assessments")
def list_assessments(db: Session = Depends(get_db)):
    assessments = db.query(Assessment).all()
    return [
        {
            "id": a.id,
            "skill_name": a.skill_name,
            "title": a.title,
            "description": a.description,
            "level": a.level,
            "duration_minutes": a.duration_minutes,
            "passing_score": a.passing_score,
            "questions_count": len(a.questions)
        }
        for a in assessments
    ]


@router.get("/assessments/{id}")
def get_assessment(id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Mask correct_idx and explanation during exam
    sanitized_questions = [
        {
            "question": q["question"],
            "options": q["options"]
        }
        for q in a.questions
    ]

    return {
        "id": a.id,
        "skill_name": a.skill_name,
        "title": a.title,
        "description": a.description,
        "level": a.level,
        "duration_minutes": a.duration_minutes,
        "passing_score": a.passing_score,
        "questions": sanitized_questions
    }


@router.post("/assessments/{id}/submit")
def submit_assessment(
    id: int,
    req: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    a = db.query(Assessment).filter(Assessment.id == id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")

    correct_count = 0
    total = len(a.questions)
    for idx, q in enumerate(a.questions):
        if idx < len(req.answers) and req.answers[idx] == q.get("correct_idx", 0):
            correct_count += 1

    score_pct = round((correct_count / max(1, total)) * 100, 1)
    passed = score_pct >= a.passing_score

    # Save attempt
    attempt = AssessmentAttempt(
        user_id=current_user.id,
        assessment_id=a.id,
        score=score_pct,
        passed=passed,
        answers_json=json.dumps(req.answers)
    )
    db.add(attempt)

    issued_cert_id = None
    if passed:
        # 1. Update user proficiency dictionary with new level
        profs = current_user.skill_proficiency or {}
        new_level = max(profs.get(a.skill_name, 1), a.level)
        profs[a.skill_name] = new_level
        current_user.skill_proficiency = profs

        # Ensure skill is in user's skills list
        user_skills = current_user.skills or []
        if a.skill_name not in user_skills:
            user_skills.append(a.skill_name)
            current_user.skills = user_skills

        # 2. Add verified skill badge
        existing_vs = db.query(VerifiedSkill).filter(
            VerifiedSkill.user_id == current_user.id,
            VerifiedSkill.skill_name == a.skill_name
        ).first()
        if not existing_vs:
            vs = VerifiedSkill(
                user_id=current_user.id,
                skill_name=a.skill_name,
                verification_type="assessment",
                proof_link=f"/api/assessments/{a.id}"
            )
            db.add(vs)

        # 3. Award Certificate
        uid = f"ACE-CERT-{datetime.utcnow().year}-SK{a.id:02d}{current_user.id:04d}-{datetime.utcnow().strftime('%H%M%S%f')[:10]}"
        cert = Certificate(
            unique_id=uid,
            user_id=current_user.id,
            recipient_name=current_user.name,
            title=f"Verified Skill Assessment: {a.skill_name} (Level {new_level})",
            issuer="ACE Skill Verification Board",
            certificate_type="assessment",
            item_id=a.id,
            qr_code_data=f"https://allcollegeevent.com/verify/{uid}",
            metadata_json=json.dumps({"skill": a.skill_name, "level": new_level, "score": f"{score_pct}%", "verified": True})
        )
        db.add(cert)
        issued_cert_id = uid

    db.commit()

    return {
        "passed": passed,
        "score": score_pct,
        "correct_count": correct_count,
        "total_questions": total,
        "skill_name": a.skill_name,
        "awarded_level": a.level if passed else None,
        "issued_certificate_id": issued_cert_id,
        "message": (
            f"Congratulations! You scored {score_pct}% and earned verified Level {a.level} in {a.skill_name}!"
            if passed else f"You scored {score_pct}%. Passing score is {a.passing_score}%. Review the course material and try again!"
        )
    }


@router.get("/learn-to-qualify")
def learn_to_qualify(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    UNIQUE FEATURE: When a team requires a skill level the student lacks (e.g. requires Flask level 3,
    student has level 1), computes the exact gaps and suggests one-click course learning paths to close them.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    user_skills = set(current_user.skills or [])
    user_profs = current_user.skill_proficiency or {}

    team_reqs = team.skill_requirements or {} # dict skill -> min_level
    gaps = []

    for skill, min_lvl in team_reqs.items():
        curr_lvl = user_profs.get(skill, 0)
        if curr_lvl < min_lvl:
            # Find relevant courses for this skill
            relevant_courses = db.query(Course).filter(Course.skill_tags_json.ilike(f"%{skill}%")).limit(2).all()
            # Find relevant assessment
            assessment = db.query(Assessment).filter(Assessment.skill_name == skill).first()

            gaps.append({
                "skill": skill,
                "current_level": curr_lvl,
                "required_level": min_lvl,
                "levels_short": min_lvl - curr_lvl,
                "suggested_courses": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "duration": c.duration,
                        "level": c.level
                    }
                    for c in relevant_courses
                ],
                "assessment_id": assessment.id if assessment else None
            })

    return {
        "team_name": team.name,
        "has_gaps": len(gaps) > 0,
        "gaps_count": len(gaps),
        "gaps": gaps
    }
