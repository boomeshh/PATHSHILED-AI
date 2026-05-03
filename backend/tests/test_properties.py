"""
Property-based tests for PathShield AI backend.

Uses Hypothesis to verify correctness properties across randomized inputs.
Each test runs a minimum of 100 examples.
"""

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from fastapi.testclient import TestClient

from app.ai_engine import score_report, KEYWORDS
from app.schemas import ReportCreate


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating test data
# ---------------------------------------------------------------------------

def valid_report_strategy():
    """Generate valid ReportCreate instances."""
    return st.builds(
        ReportCreate,
        name=st.text(min_size=1, max_size=100),
        phone=st.text(min_size=1, max_size=20),
        location=st.text(min_size=1, max_size=200),
        incident_type=st.sampled_from([
            "pothole", "accident", "signal_failure", "road_damage", "other"
        ]),
        description=st.text(min_size=1, max_size=500),
        severity=st.sampled_from(["low", "medium", "high", "critical"]),
        image_url=st.one_of(st.none(), st.text(min_size=1, max_size=200))
    )


# ---------------------------------------------------------------------------
# Property 1: Report submission round-trip
# Feature: pathshield-ai, Property 1: For any valid report payload, submitting
# it via POST /reports and then retrieving it via GET /reports/{report_id}
# should return a record whose user-supplied fields exactly match the original
# input, and whose risk_score, risk_level, and ai_reason fields are all
# present and non-null.
# Validates: Requirements 1.1, 1.2, 1.4, 2.10, 3.4
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(report=valid_report_strategy())
def test_report_round_trip(client: TestClient, report: ReportCreate):
    """Property 1: POST then GET by id returns matching data."""
    # Submit the report
    response = client.post("/reports", json=report.model_dump())
    assert response.status_code == 201
    
    created = response.json()
    report_id = created["report_id"]
    
    # Fetch the report by ID
    get_response = client.get(f"/reports/{report_id}")
    assert get_response.status_code == 200
    
    fetched = get_response.json()
    
    # Verify user-supplied fields match
    assert fetched["name"] == report.name
    assert fetched["phone"] == report.phone
    assert fetched["location"] == report.location
    assert fetched["incident_type"] == report.incident_type
    assert fetched["description"] == report.description
    assert fetched["severity"] == report.severity
    assert fetched["image_url"] == report.image_url
    
    # Verify AI fields are present and non-null
    assert fetched["risk_score"] is not None
    assert fetched["risk_level"] is not None
    assert fetched["ai_reason"] is not None
    assert isinstance(fetched["risk_score"], int)
    assert isinstance(fetched["risk_level"], str)
    assert isinstance(fetched["ai_reason"], str)
    assert len(fetched["ai_reason"]) > 0


# ---------------------------------------------------------------------------
# Property 2: Missing required fields returns 422
# Feature: pathshield-ai, Property 2: For any report payload with one or more
# required fields removed, a POST to /reports should return HTTP 422.
# Validates: Requirements 1.3
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    report=valid_report_strategy(),
    field_to_remove=st.sampled_from([
        "name", "phone", "location", "incident_type", "description", "severity"
    ])
)
def test_missing_field_returns_422(client: TestClient, report: ReportCreate, field_to_remove: str):
    """Property 2: Missing required field returns 422."""
    # Convert to dict and remove the field
    report_dict = report.model_dump()
    del report_dict[field_to_remove]
    
    # Submit the incomplete report
    response = client.post("/reports", json=report_dict)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Property 3: Risk score is always in [0, 100]
# Feature: pathshield-ai, Property 3: For any combination of severity value
# and description string, the risk_score returned by the AI Engine must be
# an integer in the range [0, 100] inclusive.
# Validates: Requirements 2.1, 2.4
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    severity=st.text(min_size=0, max_size=50),
    description=st.text(min_size=0, max_size=1000)
)
def test_risk_score_bounds(severity: str, description: str):
    """Property 3: Risk score is always in [0, 100]."""
    result = score_report(severity, description)
    
    assert isinstance(result["risk_score"], int)
    assert 0 <= result["risk_score"] <= 100


# ---------------------------------------------------------------------------
# Property 4: Adding a keyword never decreases the risk score
# Feature: pathshield-ai, Property 4: For any description string and any
# keyword from the defined keyword list, the score computed for
# description + " " + keyword must be greater than or equal to the score
# computed for description alone (with the same severity).
# Validates: Requirements 2.3
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    severity=st.sampled_from(["low", "medium", "high", "critical"]),
    description=st.text(min_size=0, max_size=500),
    keyword=st.sampled_from(KEYWORDS)
)
def test_keyword_never_decreases_score(severity: str, description: str, keyword: str):
    """Property 4: Adding a keyword never decreases the score."""
    # Score without keyword
    score_without = score_report(severity, description)["risk_score"]
    
    # Score with keyword appended
    description_with_keyword = description + " " + keyword
    score_with = score_report(severity, description_with_keyword)["risk_score"]
    
    assert score_with >= score_without


# ---------------------------------------------------------------------------
# Property 5: Risk level assignment matches threshold rules
# Feature: pathshield-ai, Property 5: For any risk_score in [0, 100], the
# assigned risk_level must satisfy exactly one of: score ∈ [0,30] → LOW,
# score ∈ [31,60] → MEDIUM, score ∈ [61,80] → HIGH, score ∈ [81,100] → CRITICAL.
# Validates: Requirements 2.5, 2.6, 2.7, 2.8
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(score=st.integers(min_value=0, max_value=100))
def test_risk_level_thresholds(score: int):
    """Property 5: Risk level assignment matches threshold rules."""
    # We need to construct a scenario that produces the given score
    # For simplicity, we'll use the AI engine's internal logic
    from app.ai_engine import _risk_level
    
    level = _risk_level(score)
    
    if 0 <= score <= 30:
        assert level == "LOW"
    elif 31 <= score <= 60:
        assert level == "MEDIUM"
    elif 61 <= score <= 80:
        assert level == "HIGH"
    elif 81 <= score <= 100:
        assert level == "CRITICAL"


# ---------------------------------------------------------------------------
# Property 6: AI reason is non-empty and reflects matched keywords
# Feature: pathshield-ai, Property 6: For any report where the description
# contains one or more keywords from the defined keyword list, the ai_reason
# string must be non-empty and must reference at least one of the matched
# keywords.
# Validates: Requirements 2.9
# ---------------------------------------------------------------------------

@settings(max_examples=100)
@given(
    severity=st.sampled_from(["low", "medium", "high", "critical"]),
    keyword=st.sampled_from(KEYWORDS),
    prefix=st.text(min_size=0, max_size=100),
    suffix=st.text(min_size=0, max_size=100)
)
def test_ai_reason_reflects_keywords(severity: str, keyword: str, prefix: str, suffix: str):
    """Property 6: AI reason reflects matched keywords."""
    # Construct a description that contains the keyword
    description = f"{prefix} {keyword} {suffix}"
    
    result = score_report(severity, description)
    ai_reason = result["ai_reason"]
    
    # Verify ai_reason is non-empty
    assert len(ai_reason) > 0
    
    # Verify ai_reason references the keyword
    assert keyword.lower() in ai_reason.lower()


# ---------------------------------------------------------------------------
# Property 7: GET /reports returns all reports in descending created_at order
# Feature: pathshield-ai, Property 7: For any set of N reports inserted into
# the database, GET /reports must return exactly N reports, and for every
# adjacent pair in the response list, the first report's created_at must be
# greater than or equal to the second's.
# Validates: Requirements 3.1
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(reports=st.lists(valid_report_strategy(), min_size=0, max_size=10))
def test_reports_ordered_by_created_at(client: TestClient, test_db, reports: list):
    """Property 7: GET /reports returns reports in descending created_at order."""
    # Clear database before this example
    from app.models import Report
    test_db.query(Report).delete()
    test_db.commit()
    
    # Submit all reports
    for report in reports:
        response = client.post("/reports", json=report.model_dump())
        assert response.status_code == 201
    
    # Fetch all reports
    response = client.get("/reports")
    assert response.status_code == 200
    
    fetched = response.json()
    
    # Verify count matches
    assert len(fetched) == len(reports)
    
    # Verify ordering (descending created_at)
    for i in range(len(fetched) - 1):
        first_time = fetched[i]["created_at"]
        second_time = fetched[i + 1]["created_at"]
        # Compare as strings (ISO format comparison works)
        assert first_time >= second_time


# ---------------------------------------------------------------------------
# Property 8: GET /reports/{id} round-trip
# Feature: pathshield-ai, Property 8: For any report that has been successfully
# submitted, fetching it by its report_id via GET /reports/{report_id} must
# return a response whose fields are identical to those returned at creation time.
# Validates: Requirements 3.2, 3.4
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(report=valid_report_strategy())
def test_report_fetch_by_id_round_trip(client: TestClient, report: ReportCreate):
    """Property 8: GET /reports/{id} returns identical data to creation response."""
    # Submit the report
    create_response = client.post("/reports", json=report.model_dump())
    assert create_response.status_code == 201
    
    created = create_response.json()
    report_id = created["report_id"]
    
    # Fetch by ID
    get_response = client.get(f"/reports/{report_id}")
    assert get_response.status_code == 200
    
    fetched = get_response.json()
    
    # Verify all fields match
    assert fetched == created


# ---------------------------------------------------------------------------
# Property 9: Unknown report_id returns 404
# Feature: pathshield-ai, Property 9: For any integer report_id that does not
# correspond to a persisted report, GET /reports/{report_id} must return HTTP 404.
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    existing_reports=st.lists(valid_report_strategy(), min_size=0, max_size=5),
    non_existent_id=st.integers(min_value=1000, max_value=9999)
)
def test_unknown_id_returns_404(client: TestClient, existing_reports: list, non_existent_id: int):
    """Property 9: Unknown report_id returns 404."""
    # Submit some reports
    created_ids = []
    for report in existing_reports:
        response = client.post("/reports", json=report.model_dump())
        assert response.status_code == 201
        created_ids.append(response.json()["report_id"])
    
    # Ensure the non_existent_id is truly non-existent
    if non_existent_id in created_ids:
        non_existent_id = max(created_ids) + 1000
    
    # Try to fetch non-existent report
    response = client.get(f"/reports/{non_existent_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Property 10: Analytics summary is consistent with stored reports
# Feature: pathshield-ai, Property 10: For any set of reports in the database,
# GET /analytics/summary must return total_reports equal to the count of all
# reports, critical_count equal to the count of reports with risk_level == "CRITICAL",
# high_count equal to the count of reports with risk_level == "HIGH", and
# most_common_incident_type equal to the mode of incident_type values (or null
# when the database is empty).
# Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(reports=st.lists(valid_report_strategy(), min_size=0, max_size=20))
def test_analytics_consistency(client: TestClient, test_db, reports: list):
    """Property 10: Analytics summary is consistent with stored reports."""
    # Clear database before this example
    from app.models import Report
    test_db.query(Report).delete()
    test_db.commit()
    
    # Submit all reports and track their risk levels
    created_reports = []
    for report in reports:
        response = client.post("/reports", json=report.model_dump())
        assert response.status_code == 201
        created_reports.append(response.json())
    
    # Fetch analytics
    analytics_response = client.get("/analytics/summary")
    assert analytics_response.status_code == 200
    
    analytics = analytics_response.json()
    
    # Verify total_reports
    assert analytics["total_reports"] == len(reports)
    
    # Verify critical_count
    critical_count = sum(1 for r in created_reports if r["risk_level"] == "CRITICAL")
    assert analytics["critical_count"] == critical_count
    
    # Verify high_count
    high_count = sum(1 for r in created_reports if r["risk_level"] == "HIGH")
    assert analytics["high_count"] == high_count
    
    # Verify most_common_incident_type
    if len(reports) == 0:
        assert analytics["most_common_incident_type"] is None
    else:
        from collections import Counter
        incident_types = [r["incident_type"] for r in created_reports]
        most_common = Counter(incident_types).most_common(1)[0][0]
        assert analytics["most_common_incident_type"] == most_common
