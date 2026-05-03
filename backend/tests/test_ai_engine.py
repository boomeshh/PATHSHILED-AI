"""
PathShield AI Phase 2 — AI engine unit tests
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ai_engine import score_incident, score_report


def test_critical_description():
    r = score_incident("accident", "Person unconscious with heavy bleeding and head injury", 3)
    assert r["severity"] == "Critical"
    assert r["risk_level"] == "CRITICAL"
    assert r["score"] >= 81


def test_score_in_bounds():
    for incident_type in ("accident", "pothole", "other"):
        for desc in ("", "minor scratch", "fire trapped unconscious heavy bleeding fracture"):
            r = score_incident(incident_type, desc, 0)
            assert 0 <= r["score"] <= 100


def test_victims_increase_score():
    r0 = score_incident("pothole", "large pothole", 0)
    r3 = score_incident("pothole", "large pothole", 3)
    assert r3["score"] >= r0["score"]


def test_reasons_is_list():
    r = score_incident("accident", "collision on highway", 1)
    assert isinstance(r["reasons"], list)
    assert len(r["reasons"]) > 0


def test_first_aid_guidance_present():
    for sev_desc in [
        ("accident", "unconscious heavy bleeding"),
        ("pothole",  "minor pothole"),
    ]:
        r = score_incident(sev_desc[0], sev_desc[1], 0)
        assert isinstance(r["first_aid_guidance"], list)
        assert len(r["first_aid_guidance"]) > 0


def test_low_incident_low_score():
    r = score_incident("street_light_issue", "one light not working", 0)
    assert r["score"] < 61


def test_legacy_score_report_shim():
    r = score_report("high", "accident on highway")
    assert "risk_score" in r
    assert "risk_level" in r
    assert "ai_reason" in r
    assert 0 <= r["risk_score"] <= 100
