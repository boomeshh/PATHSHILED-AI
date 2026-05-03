from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=False)
    location = Column(Text, nullable=False)
    incident_type = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Text, nullable=False)
    image_url = Column(Text, nullable=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(Text, nullable=False)
    ai_reason = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
