"""
PathShield AI — Pydantic schemas (Phase 3)
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Incident submission
# ---------------------------------------------------------------------------

class IncidentCreate(BaseModel):
    name:          str
    phone:         str
    location:      str
    latitude:      Optional[float] = None
    longitude:     Optional[float] = None
    incident_type: str
    description:   str
    victims_count: int = 0
    image_url:     Optional[str] = None


class NearbyService(BaseModel):
    name:     str
    distance: str
    phone:    str
    type:     str


class ExplanationFactor(BaseModel):
    factor: str
    points: int
    reason: str


class IncidentResponse(BaseModel):
    incident_id:            int
    name:                   str
    phone:                  str
    location:               str
    latitude:               Optional[float]
    longitude:              Optional[float]
    incident_type:          str
    description:            str
    victims_count:          int
    image_url:              Optional[str]
    ai_severity:            str
    risk_level:             str
    ai_score:               int
    ai_reasons:             List[str]
    first_aid:              List[str]
    explanation_breakdown:  List[ExplanationFactor]
    status:                 str
    assigned_department:    Optional[str]
    assigned_to:            Optional[str]
    assigned_at:            Optional[datetime]
    duplicate_possible:     bool
    duplicate_of:           Optional[int]
    trust_score:            int
    timeline_events:        List[Dict[str, Any]]
    created_at:             datetime
    nearby_hospitals:       List[NearbyService]
    nearby_police:          List[NearbyService]
    ambulance_contact:      List[NearbyService]
    emergency_numbers:      dict

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Status / assignment updates
# ---------------------------------------------------------------------------

class StatusUpdate(BaseModel):
    status: str   # reported | verified | assigned | in_progress | resolved


class AssignUpdate(BaseModel):
    assigned_department: str
    assigned_to:         str


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class SeverityDist(BaseModel):
    severity: str
    count:    int


class IncidentTypeDist(BaseModel):
    incident_type: str
    count:         int


class AnalyticsSummary(BaseModel):
    total_reports:              int
    critical_reports:           int
    high_risk_reports:          int
    resolved_reports:           int
    top_incident_type:          Optional[str]
    active_hotspots:            int
    severity_distribution:      List[SeverityDist]
    incident_type_distribution: List[IncidentTypeDist]


# ---------------------------------------------------------------------------
# Hotspots
# ---------------------------------------------------------------------------

class HotspotResponse(BaseModel):
    hotspot_id:             int
    area_name:              str
    latitude:               Optional[float]
    longitude:              Optional[float]
    incident_count:         int
    dominant_incident_type: str
    dominant_severity:      str
    risk_level:             str
    incident_ids:           List[int]


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineEvent(BaseModel):
    timestamp: str
    action:    str
    actor:     str
    note:      str


# ---------------------------------------------------------------------------
# Public summary (anonymized)
# ---------------------------------------------------------------------------

class PublicIncident(BaseModel):
    incident_id:   int
    incident_type: str
    location:      str
    ai_severity:   str
    risk_level:    str
    status:        str
    created_at:    datetime


class PublicSummary(BaseModel):
    total_reports:              int
    resolved_reports:           int
    active_hotspots:            int
    top_issue_type:             Optional[str]
    severity_distribution:      List[SeverityDist]
    incident_type_distribution: List[IncidentTypeDist]
    recent_incidents:           List[PublicIncident]
    hotspots:                   List[HotspotResponse]
