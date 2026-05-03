from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ReportCreate (request body)
class ReportCreate(BaseModel):
    name: str
    phone: str
    location: str
    incident_type: str
    description: str
    severity: str
    image_url: Optional[str] = None


# ReportResponse (response body)
class ReportResponse(BaseModel):
    report_id: int
    name: str
    phone: str
    location: str
    incident_type: str
    description: str
    severity: str
    image_url: Optional[str]
    risk_score: int
    risk_level: str
    ai_reason: str
    created_at: datetime

    class Config:
        from_attributes = True


# AnalyticsSummary (response body)
class AnalyticsSummary(BaseModel):
    total_reports: int
    critical_count: int
    high_count: int
    most_common_incident_type: Optional[str]
