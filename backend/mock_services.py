"""
PathShield AI — Mock Emergency Services (Phase 2)

Returns nearby hospitals, police stations, ambulance contacts,
and vehicle rescue services. Uses static mock data.
If latitude/longitude are provided they are echoed back in the response.
"""

from __future__ import annotations
from typing import Optional

MOCK_HOSPITALS = [
    {"name": "City General Hospital",      "distance": "1.2 km", "phone": "044-2345-6789", "type": "hospital"},
    {"name": "Apollo Trauma Centre",       "distance": "2.8 km", "phone": "044-2800-0000", "type": "hospital"},
    {"name": "St. Mary's Medical Centre",  "distance": "4.1 km", "phone": "044-2456-7890", "type": "hospital"},
]

MOCK_POLICE = [
    {"name": "Central Police Station",     "distance": "0.8 km", "phone": "100",           "type": "police"},
    {"name": "Highway Patrol Unit",        "distance": "3.5 km", "phone": "044-2300-1234", "type": "police"},
]

MOCK_AMBULANCE = [
    {"name": "National Ambulance Service", "distance": "1.0 km", "phone": "108",           "type": "ambulance"},
    {"name": "City Emergency Response",    "distance": "2.2 km", "phone": "044-2500-5678", "type": "ambulance"},
]

MOCK_VEHICLE_RESCUE = [
    {"name": "Road Rescue Team Alpha",     "distance": "2.0 km", "phone": "044-2600-9999", "type": "vehicle_rescue"},
    {"name": "Highway Recovery Services", "distance": "5.0 km", "phone": "044-2700-1111", "type": "vehicle_rescue"},
]

EMERGENCY_NUMBERS = {
    "ambulance": "108",
    "police":    "100",
    "fire":      "101",
    "disaster":  "1077",
}


def get_nearby_services(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> dict:
    """
    Return mock nearby emergency services.
    latitude/longitude are included in the response if provided.
    """
    result: dict = {
        "hospitals":       MOCK_HOSPITALS,
        "police":          MOCK_POLICE,
        "ambulance":       MOCK_AMBULANCE,
        "vehicle_rescue":  MOCK_VEHICLE_RESCUE,
        "emergency_numbers": EMERGENCY_NUMBERS,
    }
    if latitude is not None and longitude is not None:
        result["coordinates"] = {"latitude": latitude, "longitude": longitude}
    return result
