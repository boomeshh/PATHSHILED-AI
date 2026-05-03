"""
PathShield AI Phase 3 — Full API test suite
"""

import pytest
from fastapi.testclient import TestClient

SAMPLE = {
    "name": "John Doe",
    "phone": "9876543210",
    "location": "MG Road, Bangalore",
    "latitude": 12.9716,
    "longitude": 77.5946,
    "incident_type": "accident",
    "description": "Bike accident with head injury and heavy bleeding. Person unconscious.",
    "victims_count": 2,
    "image_url": None,
}

SAMPLE_POTHOLE = {
    "name": "Jane Smith",
    "phone": "9123456789",
    "location": "MG Road, Bangalore",
    "latitude": 12.9718,
    "longitude": 77.5948,
    "incident_type": "pothole",
    "description": "Large pothole causing vehicle damage.",
    "victims_count": 0,
}


# 1. Health check
def test_health_check(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# 2. AI engine returns Critical
def test_ai_engine_critical():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from ai_engine import score_incident
    result = score_incident(
        "accident",
        "Bike accident with head injury and heavy bleeding. Person unconscious.",
        victims_count=2,
    )
    assert result["severity"] == "Critical"
    assert result["risk_level"] == "CRITICAL"
    assert result["score"] >= 81


# 3. AI explanation_breakdown exists
def test_ai_explanation_breakdown():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from ai_engine import score_incident
    result = score_incident("accident", "collision on highway with bleeding", 1)
    assert "explanation_breakdown" in result
    assert isinstance(result["explanation_breakdown"], list)
    assert len(result["explanation_breakdown"]) > 0
    for item in result["explanation_breakdown"]:
        assert "factor" in item
        assert "points" in item
        assert "reason" in item
    total = sum(item["points"] for item in result["explanation_breakdown"])
    assert 0 <= result["score"] <= 100


# 4. Trust score is calculated
def test_trust_score(client):
    r = client.post("/incident/report", json=SAMPLE)
    assert r.status_code == 201
    data = r.json()
    assert "trust_score" in data
    assert 0 <= data["trust_score"] <= 100
    # Has phone + GPS + long description → should be high
    assert data["trust_score"] >= 50


# 5. POST creates incident with AI result
def test_create_incident(client):
    r = client.post("/incident/report", json=SAMPLE)
    assert r.status_code == 201
    data = r.json()
    assert "incident_id" in data
    assert data["ai_severity"] in ("Low", "Moderate", "High", "Critical")
    assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    assert isinstance(data["ai_reasons"], list)
    assert isinstance(data["first_aid"], list)
    assert isinstance(data["explanation_breakdown"], list)
    assert isinstance(data["nearby_hospitals"], list)
    assert data["status"] == "reported"
    assert data["duplicate_possible"] is False


# 6. Duplicate detection
def test_duplicate_detection(client):
    client.post("/incident/report", json=SAMPLE)
    r2 = client.post("/incident/report", json=SAMPLE)
    assert r2.status_code == 201
    data = r2.json()
    assert data["duplicate_possible"] is True
    assert data["duplicate_of"] is not None


# 7. GET /incident/all returns submitted incident
def test_list_incidents(client):
    client.post("/incident/report", json=SAMPLE)
    r = client.get("/incident/all")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# 8. PATCH status updates to resolved + timeline event added
def test_update_status_and_timeline(client):
    create_r = client.post("/incident/report", json=SAMPLE)
    iid = create_r.json()["incident_id"]

    patch_r = client.patch(f"/incident/{iid}/status", json={"status": "resolved"})
    assert patch_r.status_code == 200
    assert patch_r.json()["status"] == "resolved"

    tl = client.get(f"/incident/{iid}/timeline")
    assert tl.status_code == 200
    actions = [e["action"] for e in tl.json()]
    assert any("resolved" in a for a in actions)


# 9. Assignment endpoint
def test_assign_incident(client):
    iid = client.post("/incident/report", json=SAMPLE).json()["incident_id"]
    r = client.patch(f"/incident/{iid}/assign",
                     json={"assigned_department": "Police", "assigned_to": "Inspector Raj"})
    assert r.status_code == 200
    data = r.json()
    assert data["assigned_department"] == "Police"
    assert data["status"] == "assigned"

    tl = client.get(f"/incident/{iid}/timeline").json()
    assert any("assigned" in e["action"].lower() for e in tl)


# 10. Timeline created on incident report
def test_timeline_on_create(client):
    iid = client.post("/incident/report", json=SAMPLE).json()["incident_id"]
    tl = client.get(f"/incident/{iid}/timeline")
    assert tl.status_code == 200
    events = tl.json()
    assert len(events) >= 2
    actions = [e["action"] for e in events]
    assert any("reported" in a.lower() for a in actions)
    assert any("triage" in a.lower() for a in actions)


# 11. Hotspot detection
def test_hotspot_detection(client):
    base = {
        "name": "Test", "phone": "1234567890",
        "location": "Avinashi Road, Coimbatore",
        "latitude": 11.0168, "longitude": 76.9558,
        "incident_type": "accident",
        "description": "Accident on road", "victims_count": 1,
    }
    for _ in range(3):
        client.post("/incident/report", json=base)
    r = client.get("/analytics/hotspots")
    assert r.status_code == 200
    hotspots = r.json()
    assert len(hotspots) >= 1
    assert hotspots[0]["incident_count"] >= 3


# 12. Demo seed creates records
def test_demo_seed(client):
    r = client.post("/demo/seed")
    assert r.status_code == 201
    data = r.json()
    assert data["seeded"] >= 10
    all_r = client.get("/incident/all")
    assert len(all_r.json()) >= 10


# 13. Demo clear removes demo records
def test_demo_clear(client):
    client.post("/demo/seed")
    r = client.delete("/demo/clear")
    assert r.status_code == 200
    assert r.json()["cleared"] >= 10


# 14. Public summary does not expose name/phone
def test_public_summary_no_pii(client):
    client.post("/incident/report", json=SAMPLE)
    r = client.get("/public/summary")
    assert r.status_code == 200
    data = r.json()
    assert "total_reports" in data
    assert "resolved_reports" in data
    assert "active_hotspots" in data
    for inc in data.get("recent_incidents", []):
        assert "name" not in inc
        assert "phone" not in inc


# 15. Analytics summary returns correct keys
def test_analytics_summary(client):
    client.post("/incident/report", json=SAMPLE)
    r = client.get("/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    for key in ("total_reports", "critical_reports", "high_risk_reports",
                "resolved_reports", "top_incident_type", "active_hotspots",
                "severity_distribution", "incident_type_distribution"):
        assert key in data, f"Missing key: {key}"
    assert data["total_reports"] >= 1


# 16. Analytics empty DB
def test_analytics_empty_db(client):
    r = client.get("/analytics/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["total_reports"] == 0
    assert data["top_incident_type"] is None
    assert data["active_hotspots"] == 0


# 17. CSV export returns correct headers
def test_csv_export(client):
    client.post("/incident/report", json=SAMPLE)
    r = client.get("/export/incidents.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    text = r.text
    assert "id" in text
    assert "incident_type" in text
    assert "severity" in text
    assert "risk_level" in text
    assert "status" in text


# 18. CORS headers
def test_cors_user_frontend(client):
    r = client.options("/", headers={"Origin": "http://localhost:5173",
                                     "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" in r.headers


def test_cors_admin_frontend(client):
    r = client.options("/", headers={"Origin": "http://localhost:5174",
                                     "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" in r.headers


# 19. 404 for unknown incident
def test_unknown_incident_404(client):
    r = client.get("/incident/99999")
    assert r.status_code == 404
