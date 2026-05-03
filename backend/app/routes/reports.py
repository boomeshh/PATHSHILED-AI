"""
API routes for PathShield AI reports and analytics.
"""

from collections import Counter
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai_engine import score_report
from app.database import get_db
from app.models import Report
from app.schemas import AnalyticsSummary, ReportCreate, ReportResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Task 5.1 — POST /reports
# ---------------------------------------------------------------------------

@router.post("/reports", response_model=ReportResponse, status_code=201)
def create_report(body: ReportCreate, db: Session = Depends(get_db)):
    """Validate body, score with AI engine, persist, and return the report."""
    ai_result = score_report(body.severity, body.description)

    report = Report(
        name=body.name,
        phone=body.phone,
        location=body.location,
        incident_type=body.incident_type,
        description=body.description,
        severity=body.severity,
        image_url=body.image_url,
        risk_score=ai_result["risk_score"],
        risk_level=ai_result["risk_level"],
        ai_reason=ai_result["ai_reason"],
        created_at=datetime.utcnow(),
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


# ---------------------------------------------------------------------------
# Task 5.2 — GET /reports
# ---------------------------------------------------------------------------

@router.get("/reports", response_model=List[ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    """Return all reports ordered by created_at descending."""
    reports = (
        db.query(Report)
        .order_by(Report.created_at.desc())
        .all()
    )
    return reports


# ---------------------------------------------------------------------------
# Task 5.3 — GET /reports/{report_id}
# ---------------------------------------------------------------------------

@router.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    """Fetch a single report by ID, or raise 404 if not found."""
    report = db.query(Report).filter(Report.report_id == report_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# ---------------------------------------------------------------------------
# Task 5.4 — GET /analytics/summary
# ---------------------------------------------------------------------------

@router.get("/analytics/summary", response_model=AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db)):
    """Compute and return aggregate statistics over all reports."""
    all_reports = db.query(Report).all()

    total_reports = len(all_reports)
    critical_count = sum(1 for r in all_reports if r.risk_level == "CRITICAL")
    high_count = sum(1 for r in all_reports if r.risk_level == "HIGH")

    if total_reports == 0:
        most_common_incident_type = None
    else:
        counter = Counter(r.incident_type for r in all_reports)
        most_common_incident_type = counter.most_common(1)[0][0]

    return AnalyticsSummary(
        total_reports=total_reports,
        critical_count=critical_count,
        high_count=high_count,
        most_common_incident_type=most_common_incident_type,
    )


# ---------------------------------------------------------------------------
# Task 5.5 — GET /health
# ---------------------------------------------------------------------------

@router.get("/health")
def health_check():
    """Liveness check — returns 200 with status indicator."""
    return {"status": "ok"}
