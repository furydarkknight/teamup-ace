"""
TeamUp by ACE - Platform Expansion Models
Covers Opportunities, Jobs, Resumes, Applications, Courses, Assessments,
Certificates, Portfolios, Mentors, Alumni, Forums, Colleges, Clubs,
Project Submissions, and Advanced Team Collaboration.
"""

from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


# ==========================================
# PHASE 1: OPPORTUNITIES HUB
# ==========================================
class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), index=True)
    organizer_name = Column(String(150), nullable=False, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Types: Hackathon, Competition, Quiz, Case Study, Coding Challenge, Workshop, Webinar,
    # Conference, Scholarship, Fellowship, Internship, Full-time Job, Part-time Job,
    # Freelance Project, Mentorship Program, Campus Ambassador Role
    type = Column(String(100), nullable=False, index=True)
    
    description = Column(Text, default="")
    eligibility = Column(Text, default="Open to all college students")
    eligibility_year = Column(String(100), default="All Years")
    eligibility_branch = Column(String(100), default="All Branches")
    eligibility_college_type = Column(String(100), default="All Colleges")
    
    skills_json = Column(Text, default="[]") # ["Python", "Machine Learning"]
    location_mode = Column(String(50), default="Online", index=True) # Online, Offline, Hybrid
    location_venue = Column(String(200), default="Virtual")
    
    start_date = Column(String(100), default="")
    end_date = Column(String(100), default="")
    deadline = Column(String(100), default="")
    
    team_size_min = Column(Integer, default=1)
    team_size_max = Column(Integer, default=4)
    
    prize_pool = Column(String(100), default="₹50,000")
    stipend_ctc = Column(String(100), default="")
    perks_json = Column(Text, default='["Certificate of Excellence", "Mentorship Access"]')
    rounds_json = Column(Text, default='[{"name": "Preliminary Round", "date": "TBD"}]')
    faqs_json = Column(Text, default="[]")
    attachments_json = Column(Text, default="[]")
    banner_url = Column(String(255), default="https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=1200&q=80")
    tags_json = Column(Text, default="[]")
    
    status = Column(String(50), default="Active", index=True) # Active, Closing Soon, Completed
    is_featured = Column(Boolean, default=False, index=True)
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    applications = relationship("Application", back_populates="opportunity")
    submissions = relationship("ProjectSubmission", back_populates="opportunity")

    @property
    def skills(self):
        try:
            return json.loads(self.skills_json) if self.skills_json else []
        except Exception:
            return []

    @skills.setter
    def skills(self, val):
        self.skills_json = json.dumps(val if isinstance(val, list) else [])

    @property
    def perks(self):
        try:
            return json.loads(self.perks_json) if self.perks_json else []
        except Exception:
            return []

    @property
    def rounds(self):
        try:
            return json.loads(self.rounds_json) if self.rounds_json else []
        except Exception:
            return []

    @property
    def faqs(self):
        try:
            return json.loads(self.faqs_json) if self.faqs_json else []
        except Exception:
            return []

    @property
    def tags(self):
        try:
            return json.loads(self.tags_json) if self.tags_json else []
        except Exception:
            return []


# ==========================================
# PHASE 2: JOBS, INTERNSHIPS & RESUMES
# ==========================================
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    slug = Column(String(150), index=True)
    logo_url = Column(String(255), default="https://images.unsplash.com/photo-1549923746-c502d488b3ea?auto=format&fit=crop&w=200&q=80")
    website = Column(String(255), default="")
    industry = Column(String(100), default="Technology", index=True)
    size = Column(String(50), default="50-200 Employees")
    location = Column(String(100), default="Bangalore, India")
    about = Column(Text, default="")
    culture = Column(Text, default="")
    benefits_json = Column(Text, default='["Health Insurance", "Flexible Hours", "Learning Budget"]')
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job_postings = relationship("JobPosting", back_populates="company")

    @property
    def benefits(self):
        try:
            return json.loads(self.benefits_json) if self.benefits_json else []
        except Exception:
            return []


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    role_category = Column(String(100), default="Software Engineering", index=True)
    job_type = Column(String(50), default="Internship", index=True) # Internship, Full-time, Part-time
    work_mode = Column(String(50), default="Remote", index=True)    # Remote, On-site, Hybrid
    location = Column(String(100), default="Remote")
    duration = Column(String(50), default="3-6 Months")
    openings_count = Column(Integer, default=2)
    stipend_salary = Column(String(100), default="₹25,000 - ₹40,000/month")
    skills_required_json = Column(Text, default="[]")
    experience_required = Column(String(50), default="Beginner to Intermediate")
    description = Column(Text, default="")
    perks_json = Column(Text, default='["PPO Potential", "Mentorship", "Certificate"]')
    selection_process_json = Column(Text, default='["Profile Shortlisting", "Technical Assessment", "Final Interview"]')
    screening_questions_json = Column(Text, default="[]")
    deadline = Column(String(100), default="In 30 days")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="job_postings")
    applications = relationship("Application", back_populates="job_posting")

    @property
    def skills_required(self):
        try:
            return json.loads(self.skills_required_json) if self.skills_required_json else []
        except Exception:
            return []

    @property
    def perks(self):
        try:
            return json.loads(self.perks_json) if self.perks_json else []
        except Exception:
            return []

    @property
    def selection_process(self):
        try:
            return json.loads(self.selection_process_json) if self.selection_process_json else []
        except Exception:
            return []

    @property
    def screening_questions(self):
        try:
            return json.loads(self.screening_questions_json) if self.screening_questions_json else []
        except Exception:
            return []


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(150), default="Primary Resume")
    template_name = Column(String(50), default="modern") # modern, minimal, technical
    data_json = Column(Text, default="{}") # {summary, education, experience, projects, skills, certifications}
    is_default = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

    @property
    def data(self):
        try:
            return json.loads(self.data_json) if self.data_json else {}
        except Exception:
            return {}

    @data.setter
    def data(self, val):
        self.data_json = json.dumps(val if isinstance(val, dict) else {})


class JobAlert(Base):
    __tablename__ = "job_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    keyword = Column(String(100), default="")
    role = Column(String(100), default="")
    location = Column(String(100), default="")
    min_stipend = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# ==========================================
# PHASE 3: APPLICATIONS & NOTIFICATIONS
# ==========================================
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True, index=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=True, index=True)
    application_type = Column(String(50), default="opportunity", index=True) # opportunity, job
    
    # Status: Applied -> Under Review -> Shortlisted -> Interview -> Offer -> Selected / Rejected / Withdrawn
    status = Column(String(50), default="Applied", index=True)
    status_timeline_json = Column(Text, default="[]") # [{status, timestamp, note}]
    
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    cover_note = Column(Text, default="")
    screening_answers_json = Column(Text, default="{}")
    expected_stipend = Column(String(100), default="")
    
    interview_date = Column(DateTime, nullable=True)
    interview_link = Column(String(255), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")
    opportunity = relationship("Opportunity", back_populates="applications")
    job_posting = relationship("JobPosting", back_populates="applications")
    resume = relationship("Resume")

    @property
    def status_timeline(self):
        try:
            return json.loads(self.status_timeline_json) if self.status_timeline_json else []
        except Exception:
            return []

    @property
    def screening_answers(self):
        try:
            return json.loads(self.screening_answers_json) if self.screening_answers_json else {}
        except Exception:
            return []


class SavedItem(Base):
    __tablename__ = "saved_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False, index=True) # opportunity, job, course, team
    item_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, default="")
    link = Column(String(255), default="")
    notification_type = Column(String(50), default="system", index=True) # match, application, deadline, invite, mentor, system
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


# ==========================================
# PHASE 4: LEARN: COURSES & ASSESSMENTS
# ==========================================
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    slug = Column(String(200), index=True)
    description = Column(Text, default="")
    skill_tags_json = Column(Text, default="[]") # ["FastAPI", "Python", "Backend"]
    level = Column(String(50), default="Beginner", index=True) # Beginner, Intermediate, Advanced
    duration = Column(String(50), default="6 Hours")
    mode = Column(String(50), default="Self-paced")
    is_free = Column(Boolean, default=True)
    mock_price = Column(Integer, default=0)
    instructor_name = Column(String(100), default="ACE Industry Fellows")
    instructor_title = Column(String(150), default="Senior Staff Engineer")
    rating = Column(Float, default=4.8)
    enrolled_count = Column(Integer, default=120)
    thumbnail_url = Column(String(255), default="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=600&q=80")
    created_at = Column(DateTime, default=datetime.utcnow)

    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("CourseEnrollment", back_populates="course")

    @property
    def skill_tags(self):
        try:
            return json.loads(self.skill_tags_json) if self.skill_tags_json else []
        except Exception:
            return []


class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    order_num = Column(Integer, default=1)

    course = relationship("Course", back_populates="modules")
    lessons = relationship("CourseLesson", back_populates="module", cascade="all, delete-orphan")


class CourseLesson(Base):
    __tablename__ = "course_lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    order_num = Column(Integer, default=1)
    content_type = Column(String(50), default="text") # text, video, quiz
    content = Column(Text, default="")
    video_url = Column(String(255), default="")
    quiz_data_json = Column(Text, default="[]") # [{question, options, answer_index}]

    module = relationship("CourseModule", back_populates="lessons")

    @property
    def quiz_data(self):
        try:
            return json.loads(self.quiz_data_json) if self.quiz_data_json else []
        except Exception:
            return []


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    progress_percent = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    course = relationship("Course", back_populates="enrollments")


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id"), nullable=False, index=True)
    is_completed = Column(Boolean, default=True)
    completed_at = Column(DateTime, default=datetime.utcnow)


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(100), nullable=False, index=True) # Must match SKILLS list
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    level = Column(Integer, default=3) # 1-5 proficiency level awarded on pass
    questions_json = Column(Text, default="[]") # [{question, options: [], correct_idx: 0, explanation: ""}]
    duration_minutes = Column(Integer, default=15)
    passing_score = Column(Integer, default=70) # percentage

    @property
    def questions(self):
        try:
            return json.loads(self.questions_json) if self.questions_json else []
        except Exception:
            return []


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)
    score = Column(Float, default=0.0) # 0-100%
    passed = Column(Boolean, default=False)
    answers_json = Column(Text, default="[]")
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    assessment = relationship("Assessment")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    role_target = Column(String(100), nullable=False, index=True) # From PREFERRED_ROLES
    description = Column(Text, default="")
    course_ids_json = Column(Text, default="[]") # [1, 2, 3]
    capstone_project_json = Column(Text, default="{}") # {title, description, repo_template}
    recommended_hackathon_id = Column(Integer, nullable=True)
    badge_icon = Column(String(100), default="fa-graduation-cap")

    @property
    def course_ids(self):
        try:
            return json.loads(self.course_ids_json) if self.course_ids_json else []
        except Exception:
            return []

    @property
    def capstone_project(self):
        try:
            return json.loads(self.capstone_project_json) if self.capstone_project_json else {}
        except Exception:
            return {}


# ==========================================
# PHASE 5: CERTIFICATES & PORTFOLIO
# ==========================================
class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(100), unique=True, index=True, nullable=False) # e.g. "ACE-CERT-2026-X892"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    recipient_name = Column(String(150), nullable=False)
    title = Column(String(200), nullable=False)
    issuer = Column(String(150), default="AllCollegeEvent.com (ACE)")
    certificate_type = Column(String(50), default="course", index=True) # course, assessment, hackathon_win, hackathon_participation, internship, workshop
    item_id = Column(Integer, nullable=True)
    issue_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="Valid", index=True) # Valid, Revoked
    qr_code_data = Column(String(255), default="")
    metadata_json = Column(Text, default="{}")

    user = relationship("User")

    @property
    def metadata_dict(self):
        try:
            return json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            return {}


class VerifiedSkill(Base):
    __tablename__ = "verified_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    verification_type = Column(String(50), default="assessment") # assessment, certificate, github
    proof_link = Column(String(255), default="")
    verified_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, default="")
    icon = Column(String(100), default="fa-award")
    category = Column(String(50), default="general") # hackathon, teams, community, learning


class UserBadge(Base):
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False, index=True)
    awarded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    badge = relationship("Badge")


# ==========================================
# PHASE 6: COMMUNITY, MENTORS & ALUMNI
# ==========================================
class MentorProfile(Base):
    __tablename__ = "mentor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    company = Column(String(150), default="")
    job_title = Column(String(150), default="")
    expertise_skills_json = Column(Text, default="[]")
    years_experience = Column(Integer, default=3)
    bio = Column(Text, default="")
    max_mentees = Column(Integer, default=5)
    available_slots_json = Column(Text, default='["Friday 6:00 PM", "Saturday 11:00 AM", "Sunday 4:00 PM"]')
    rating = Column(Float, default=4.9)
    sessions_count = Column(Integer, default=12)
    is_approved = Column(Boolean, default=True)

    user = relationship("User")

    @property
    def expertise_skills(self):
        try:
            return json.loads(self.expertise_skills_json) if self.expertise_skills_json else []
        except Exception:
            return []

    @property
    def available_slots(self):
        try:
            return json.loads(self.available_slots_json) if self.available_slots_json else []
        except Exception:
            return []


class MentorshipSession(Base):
    __tablename__ = "mentorship_sessions"

    id = Column(Integer, primary_key=True, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mentee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    scheduled_at = Column(String(100), default="Saturday 11:00 AM")
    duration_mins = Column(Integer, default=30)
    topic = Column(String(200), default="Career & Hackathon Prep")
    status = Column(String(50), default="Scheduled", index=True) # Requested, Scheduled, Completed, Cancelled
    notes = Column(Text, default="")
    rating = Column(Integer, nullable=True) # 1-5
    review = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    mentor = relationship("User", foreign_keys=[mentor_id])
    mentee = relationship("User", foreign_keys=[mentee_id])


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    college = Column(String(150), nullable=False, index=True)
    graduation_year = Column(String(50), default="2023")
    company = Column(String(150), nullable=False, index=True)
    current_role = Column(String(150), default="Software Development Engineer")
    can_refer = Column(Boolean, default=True)
    linkedin_url = Column(String(255), default="")

    user = relationship("User")


class ReferralRequest(Base):
    __tablename__ = "referral_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alumni_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_url = Column(String(255), default="")
    resume_link = Column(String(255), default="")
    note = Column(Text, default="")
    status = Column(String(50), default="Pending", index=True) # Pending, Referred, Declined
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", foreign_keys=[student_id])
    alumni = relationship("User", foreign_keys=[alumni_id])


class ForumThread(Base):
    __tablename__ = "forum_threads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True, index=True)
    skill_name = Column(String(100), nullable=True, index=True)
    title = Column(String(250), nullable=False)
    content = Column(Text, default="")
    upvotes_count = Column(Integer, default=1)
    replies_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    posts = relationship("ForumPost", back_populates="thread", cascade="all, delete-orphan")


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("forum_threads.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, default="")
    upvotes_count = Column(Integer, default=0)
    is_accepted_answer = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    thread = relationship("ForumThread", back_populates="posts")
    user = relationship("User")


class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    city = Column(String(100), default="Delhi")
    state = Column(String(100), default="Delhi")
    domain = Column(String(100), default=".ac.in")
    verified = Column(Boolean, default=True)
    logo_url = Column(String(255), default="https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=200&q=80")
    description = Column(Text, default="")
    student_count = Column(Integer, default=450)

    clubs = relationship("Club", back_populates="college")


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(100), default="Coding", index=True) # Coding, Robotics, AI/ML, Design
    description = Column(Text, default="")
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    members_count = Column(Integer, default=42)

    college = relationship("College", back_populates="clubs")


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    tagline = Column(String(255), default="")
    description = Column(Text, default="")
    repo_url = Column(String(255), default="")
    demo_url = Column(String(255), default="")
    attachments_json = Column(Text, default="[]")
    submitted_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")
    opportunity = relationship("Opportunity", back_populates="submissions")
    scores = relationship("JudgingScore", back_populates="submission")


class JudgingScore(Base):
    __tablename__ = "judging_scores"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("project_submissions.id"), nullable=False, index=True)
    judge_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    innovation_score = Column(Float, default=8.0) # 1-10
    technical_score = Column(Float, default=8.5)  # 1-10
    presentation_score = Column(Float, default=9.0) # 1-10
    total_score = Column(Float, default=25.5)     # sum
    feedback = Column(Text, default="")

    submission = relationship("ProjectSubmission", back_populates="scores")
    judge = relationship("User")


# ==========================================
# PHASE 8: ADVANCED TEAM COLLABORATION
# ==========================================
class TrialSprint(Base):
    __tablename__ = "trial_sprints"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prompt = Column(Text, default="Design and implement a mock schema for the hackathon MVP within 24 hours.")
    start_time = Column(DateTime, default=datetime.utcnow)
    duration_hours = Column(Integer, default=24)
    status = Column(String(50), default="Active") # Active, Completed, Exited
    submission_text = Column(Text, default="")

    team = relationship("Team")
    user = relationship("User")


class BackupBench(Base):
    __tablename__ = "backup_bench"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    rank_order = Column(Integer, default=1)
    note = Column(String(255), default="High-fit replacement for frontend/backend")

    team = relationship("Team")
    user = relationship("User")


class TeamTask(Base):
    __tablename__ = "team_tasks"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="todo") # todo, in_progress, done
    priority = Column(String(50), default="medium") # low, medium, high
    due_date = Column(String(50), default="Tomorrow")
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team")
    assigned_to = relationship("User")
