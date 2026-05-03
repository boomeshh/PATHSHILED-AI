"""
PathShield AI — AI Engine (Phase 3)

Rule-based explainable scoring with breakdown.
Inputs: incident_type, description, victims_count
Outputs: severity, risk_level, score, reasons, first_aid_guidance, explanation_breakdown
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Keyword tables
# ---------------------------------------------------------------------------

CRITICAL_KEYWORDS: list[str] = [
    "unconscious", "heavy bleeding", "head injury", "not breathing",
    "fracture", "fire", "trapped",
]

HIGH_KEYWORDS: list[str] = [
    "accident", "collision", "bleeding", "severe pain",
    "highway", "multiple vehicles",
]

MEDIUM_KEYWORDS: list[str] = [
    "pothole", "road block", "signal issue", "street light",
    "minor injury", "flooding", "debris",
]

INCIDENT_BASE_SCORES: dict[str, int] = {
    "accident":           60,
    "pothole":            20,
    "road_block":         30,
    "signal_issue":       25,
    "street_light_issue": 20,
    "other":              15,
}

INCIDENT_BASE_REASONS: dict[str, str] = {
    "accident":           "Accidents require urgent emergency attention",
    "pothole":            "Potholes cause vehicle damage and falls",
    "road_block":         "Road blocks disrupt traffic and emergency access",
    "signal_issue":       "Signal failures increase collision risk",
    "street_light_issue": "Poor lighting increases accident risk at night",
    "other":              "General road hazard reported",
}

FIRST_AID_GUIDANCE: dict[str, list[str]] = {
    "Critical": [
        "Call 108 (ambulance) immediately.",
        "Do not move the victim unless there is immediate danger.",
        "If unconscious and breathing, place in recovery position.",
        "Apply firm pressure to any bleeding wounds.",
        "Keep the victim warm and calm until help arrives.",
        "Do not give food or water.",
    ],
    "High": [
        "Call 108 if injuries are visible.",
        "Keep the injured person still and comfortable.",
        "Apply pressure to minor bleeding wounds with a clean cloth.",
        "Do not remove any embedded objects.",
        "Monitor breathing and pulse.",
    ],
    "Moderate": [
        "Assess the scene for safety before approaching.",
        "Call 100 (police) to report the hazard.",
        "Warn oncoming traffic if safe to do so.",
        "Provide basic comfort to anyone affected.",
    ],
    "Low": [
        "Report the hazard to local authorities.",
        "Place warning signs or cones if available.",
        "Avoid the hazard area until it is cleared.",
    ],
}


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------

def score_incident(
    incident_type: str,
    description: str,
    victims_count: int = 0,
) -> dict:
    """
    Compute an AI risk assessment for a road incident.

    Returns:
        severity             (str)        – Low / Moderate / High / Critical
        risk_level           (str)        – LOW / MEDIUM / HIGH / CRITICAL
        score                (int)        – 0–100
        reasons              (list[str])  – human-readable bullets
        first_aid_guidance   (list[str])  – actionable steps
        explanation_breakdown(list[dict]) – [{factor, points, reason}]
    """
    desc_lower = description.lower()
    reasons: list[str] = []
    breakdown: list[dict] = []

    # 1. Base score from incident type
    base = INCIDENT_BASE_SCORES.get(incident_type.lower(), 15)
    base_reason = INCIDENT_BASE_REASONS.get(incident_type.lower(), "Road hazard reported")
    reasons.append(f"Incident type '{incident_type}' contributes a base score of {base}.")
    breakdown.append({
        "factor": f"Incident type: {incident_type.replace('_', ' ').title()}",
        "points": base,
        "reason": base_reason,
    })

    # 2. Keyword scoring
    critical_hits = [kw for kw in CRITICAL_KEYWORDS if kw in desc_lower]
    high_hits     = [kw for kw in HIGH_KEYWORDS     if kw in desc_lower]
    medium_hits   = [kw for kw in MEDIUM_KEYWORDS   if kw in desc_lower]

    for kw in critical_hits:
        breakdown.append({
            "factor": f"Keyword: {kw}",
            "points": 15,
            "reason": f"'{kw}' indicates a life-threatening situation",
        })
    for kw in high_hits:
        breakdown.append({
            "factor": f"Keyword: {kw}",
            "points": 8,
            "reason": f"'{kw}' indicates a high-risk situation",
        })
    for kw in medium_hits:
        breakdown.append({
            "factor": f"Keyword: {kw}",
            "points": 4,
            "reason": f"'{kw}' indicates a moderate road hazard",
        })

    keyword_bonus = len(critical_hits) * 15 + len(high_hits) * 8 + len(medium_hits) * 4

    if critical_hits:
        reasons.append(f"Critical indicators: {', '.join(critical_hits)} (+{len(critical_hits)*15} pts).")
    if high_hits:
        reasons.append(f"High-risk indicators: {', '.join(high_hits)} (+{len(high_hits)*8} pts).")
    if medium_hits:
        reasons.append(f"Medium-risk indicators: {', '.join(medium_hits)} (+{len(medium_hits)*4} pts).")

    # 3. Victims count bonus
    victims_bonus = 0
    if victims_count >= 5:
        victims_bonus = 20
        reasons.append(f"{victims_count} victims — major incident (+20 pts).")
        breakdown.append({"factor": f"Victims count: {victims_count}", "points": 20, "reason": "5+ victims indicates a mass casualty event"})
    elif victims_count >= 3:
        victims_bonus = 12
        reasons.append(f"{victims_count} victims — multiple casualties (+12 pts).")
        breakdown.append({"factor": f"Victims count: {victims_count}", "points": 12, "reason": "3+ victims indicates multiple casualties"})
    elif victims_count >= 1:
        victims_bonus = 5
        reasons.append(f"{victims_count} victim(s) reported (+5 pts).")
        breakdown.append({"factor": f"Victims count: {victims_count}", "points": 5, "reason": "At least one victim reported"})

    raw_score = base + keyword_bonus + victims_bonus
    score = min(raw_score, 100)

    # 4. Severity / risk level
    if score >= 81:
        severity, risk_level = "Critical", "CRITICAL"
    elif score >= 61:
        severity, risk_level = "High", "HIGH"
    elif score >= 31:
        severity, risk_level = "Moderate", "MEDIUM"
    else:
        severity, risk_level = "Low", "LOW"

    reasons.append(f"Final AI score: {score}/100 → {severity}.")

    return {
        "severity":             severity,
        "risk_level":           risk_level,
        "score":                score,
        "reasons":              reasons,
        "first_aid_guidance":   FIRST_AID_GUIDANCE[severity],
        "explanation_breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Trust score calculation
# ---------------------------------------------------------------------------

def calculate_trust_score(
    phone: str,
    latitude,
    longitude,
    description: str,
    image_url,
    victims_count: int,
    duplicate_possible: bool,
) -> int:
    score = 0
    if phone:                          score += 20
    if latitude is not None:           score += 20
    if description and len(description) > 30: score += 20
    if image_url:                      score += 15
    if not duplicate_possible:         score += 15
    if victims_count >= 0:             score += 10
    return min(score, 100)


# ---------------------------------------------------------------------------
# Legacy shim
# ---------------------------------------------------------------------------

def score_report(severity: str, description: str) -> dict:
    _map = {"low": "other", "medium": "pothole", "high": "accident", "critical": "accident"}
    result = score_incident(_map.get(severity.lower(), "other"), description, 0)
    return {
        "risk_score": result["score"],
        "risk_level": result["risk_level"],
        "ai_reason":  " ".join(result["reasons"]),
    }
