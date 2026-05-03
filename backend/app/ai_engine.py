"""
AI Engine for PathShield AI.

Provides a single pure, stateless function `score_report` that computes
a risk score, risk level, and human-readable reason for a submitted report.
"""

SEVERITY_BASE_SCORES: dict[str, int] = {
    "low": 10,
    "medium": 40,
    "high": 70,
    "critical": 90,
}

KEYWORD_INCREMENT = 5  # points added per matched keyword

KEYWORDS: list[str] = [
    "accident",
    "crash",
    "blood",
    "emergency",
    "injured",
    "death",
    "fire",
    "ambulance",
    "signal",
    "pothole",
    "overspeed",
]


def _risk_level(score: int) -> str:
    """Map a numeric score to a risk level label."""
    if score <= 30:
        return "LOW"
    elif score <= 60:
        return "MEDIUM"
    elif score <= 80:
        return "HIGH"
    else:
        return "CRITICAL"


def score_report(severity: str, description: str) -> dict:
    """
    Compute a risk assessment for a road safety incident report.

    Args:
        severity:    Severity string from the report (e.g. "low", "high").
                     Unknown values default to a base score of 0.
        description: Free-text description of the incident.
                     Keyword matching is case-insensitive.

    Returns:
        A dict with keys:
            risk_score  (int)  – capped at 100
            risk_level  (str)  – "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
            ai_reason   (str)  – human-readable explanation
    """
    base_score = SEVERITY_BASE_SCORES.get(severity.lower(), 0)

    description_lower = description.lower()
    matched_keywords = [kw for kw in KEYWORDS if kw in description_lower]

    keyword_bonus = len(matched_keywords) * KEYWORD_INCREMENT
    raw_score = base_score + keyword_bonus
    risk_score = min(raw_score, 100)

    level = _risk_level(risk_score)

    if matched_keywords:
        total_bonus = len(matched_keywords) * KEYWORD_INCREMENT
        keywords_str = ", ".join(matched_keywords)
        ai_reason = (
            f"Base score {base_score} from severity '{severity}'. "
            f"Keywords matched: {keywords_str} (+{total_bonus})."
        )
    else:
        ai_reason = f"Base score {base_score} from severity '{severity}'."

    return {
        "risk_score": risk_score,
        "risk_level": level,
        "ai_reason": ai_reason,
    }
