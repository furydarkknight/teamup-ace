"""
Certificates & Verification API Routes (Phase 5)
Auto-generated certificates with unique IDs, QR codes, public verification at /verify/{id}.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
import json
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.models_expansion import Certificate

router = APIRouter(prefix="/api/certificates", tags=["Certificates & Verification"])


class IssueCertificateRequest(BaseModel):
    user_email: str
    title: str
    certificate_type: str = "workshop" # course, assessment, hackathon_win, hackathon_participation, internship, workshop
    grade_or_score: Optional[str] = "Distinction"


@router.get("/my")
def get_my_certificates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    certs = db.query(Certificate).filter(Certificate.user_id == current_user.id).order_by(desc(Certificate.issue_date)).all()
    return [
        {
            "id": c.id,
            "unique_id": c.unique_id,
            "title": c.title,
            "issuer": c.issuer,
            "certificate_type": c.certificate_type,
            "issue_date": c.issue_date.strftime("%B %d, %Y") if c.issue_date else "",
            "status": c.status,
            "qr_code_data": c.qr_code_data,
            "verification_url": f"/verify/{c.unique_id}",
            "metadata": c.metadata_dict
        }
        for c in certs
    ]


@router.get("/verify/{unique_id}")
def verify_certificate(
    unique_id: str,
    db: Session = Depends(get_db)
):
    """
    Public verification endpoint accessible by anyone.
    Validates certificate status, holder, issuer, and issue date.
    """
    cert = db.query(Certificate).filter(Certificate.unique_id == unique_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Invalid certificate. No record found matching this credential ID.")

    return {
        "valid": cert.status == "Valid",
        "unique_id": cert.unique_id,
        "recipient_name": cert.recipient_name,
        "title": cert.title,
        "issuer": cert.issuer,
        "certificate_type": cert.certificate_type,
        "issue_date": cert.issue_date.strftime("%B %d, %Y") if cert.issue_date else "Verified Date",
        "status": cert.status,
        "holder_college": cert.user.college if cert.user else "Verified Institution",
        "metadata": cert.metadata_dict
    }


@router.post("/issue")
def issue_certificate(
    req: IssueCertificateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check permissions: only organizer or admin can issue
    if current_user.role not in ["organizer", "admin"]:
        raise HTTPException(status_code=403, detail="Only organizers or platform admins can issue official certificates.")

    target_user = db.query(User).filter(User.email == req.user_email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail=f"User with email '{req.user_email}' not found")

    uid = f"ACE-CERT-{datetime.utcnow().year}-ORG{target_user.id:04d}{datetime.utcnow().strftime('%M%S')}"
    cert = Certificate(
        unique_id=uid,
        user_id=target_user.id,
        recipient_name=target_user.name,
        title=req.title,
        issuer=current_user.name or "AllCollegeEvent (ACE)",
        certificate_type=req.certificate_type,
        qr_code_data=f"https://allcollegeevent.com/verify/{uid}",
        metadata_json=json.dumps({"grade": req.grade_or_score, "issued_by": current_user.name, "verified": True})
    )
    db.add(cert)
    db.commit()

    return {
        "message": f"Certificate successfully issued to {target_user.name}!",
        "unique_id": uid,
        "verification_url": f"/verify/{uid}"
    }
