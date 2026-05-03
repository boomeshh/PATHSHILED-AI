"""
PathShield AI — SQLAlchemy ORM models (Phase 3)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, Float, DateTime, Boolean
from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    incident_id        = Column(Integer, primary_key=True, autoincrement=True)
    name               = Column(Text,    nullable=False)
    phone              = Column(Text,    nullable=False)
    location           = Column(Text,    nullable=False)
    latitude           = Column(Float,   nullable=True)
    longitude          = Column(Float,   nullable=True)
    incident_type      = Column(Text,    nullable=False)
    description        = Column(Text,    nullable=False)
    victims_count      = Column(Integer, nullable=False, default=0)
    image_url          = Column(Text,    nullable=True)

    # AI output
    ai_severity        = Column(Text,    nullable=False)
    risk_level         = Column(Text,    nullable=False)
    ai_score           = Column(Integer, nullable=False)
    ai_reasons         = Column(Text,    nullable=False)   # JSON list
    first_aid          = Column(Text,    nullable=False)   # JSON list
    explanation_breakdown = Column(Text, nullable=True)    # JSON list of {factor,points,reason}

    # Status & workflow
    status             = Column(Text,    nullable=False, default="reported")
    assigned_department = Column(Text,   nullable=True)
    assigned_to        = Column(Text,    nullable=True)
    assigned_at        = Column(DateTime, nullable=True)

    # Duplicate detection
    duplicate_possible = Column(Boolean, nullable=False, default=False)
    duplicate_of       = Column(Integer, nullable=True)

    # Trust score
    trust_score        = Column(Integer, nullable=False, default=0)

    # Demo flag (for seed/clear)
    is_demo            = Column(Boolean, nullable=False, default=False)

    # Timeline (JSON list of events)
    timeline_events    = Column(Text,    nullable=True)    # JSON list

    created_at         = Column(DateTime, nullable=False,
                                default=lambda: datetime.now(timezone.utc))
