import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const SEVERITY_COLORS = {
  CRITICAL: "#dc2626",
  HIGH:     "#ea580c",
  MEDIUM:   "#ca8a04",
  LOW:      "#16a34a",
};

/**
 * Parse coordinates from various location string formats.
 * Returns { lat, lng } or null if not parseable / out of range.
 *
 * Supported formats:
 *   "11.016800,76.955800"
 *   "11.016800, 76.955800"
 *   "11.016800,  76.955800"
 *   "Lat: 11.016800, Lng: 76.955800"
 *   "11.0168, 76.9558"
 */
export function parseLocationCoordinates(location) {
  if (!location || typeof location !== "string") return null;

  // Strip emoji and common prefixes, then extract two numbers
  const cleaned = location
    .replace(/[\u{1F300}-\u{1FFFF}]/gu, "")  // strip emoji
    .replace(/lat\s*:/gi, "")
    .replace(/lng\s*:/gi, "")
    .replace(/lon\s*:/gi, "")
    .trim();

  // Match two decimal numbers separated by comma or whitespace
  const match = cleaned.match(/(-?\d{1,3}(?:\.\d+)?)\s*[,\s]\s*(-?\d{1,3}(?:\.\d+)?)/);
  if (!match) return null;

  const lat = parseFloat(match[1]);
  const lng = parseFloat(match[2]);

  if (isNaN(lat) || isNaN(lng)) return null;
  if (lat < -90  || lat > 90)   return null;
  if (lng < -180 || lng > 180)  return null;

  return { lat, lng };
}

/**
 * Inner component that adjusts map view whenever markers change.
 * Must be rendered inside <MapContainer>.
 */
function MapBoundsController({ points }) {
  const map = useMap();

  useEffect(() => {
    if (!points || points.length === 0) return;

    if (points.length === 1) {
      map.setView([points[0].lat, points[0].lng], 14);
    } else {
      const bounds = points.map(p => [p.lat, p.lng]);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [map, points]);

  return null;
}

export default function IncidentMap({ incidents }) {
  // Build list of renderable points — prefer API lat/lng, fall back to parsing location string
  const points = (incidents || []).reduce((acc, inc) => {
    let lat = inc.latitude;
    let lng = inc.longitude;

    // If API fields are missing, try parsing the location string
    if (lat == null || lng == null) {
      const parsed = parseLocationCoordinates(inc.location);
      if (parsed) { lat = parsed.lat; lng = parsed.lng; }
    }

    if (lat != null && lng != null) {
      acc.push({ lat, lng, incident: inc });
    }
    return acc;
  }, []);

  if (points.length === 0) {
    return (
      <div style={{
        background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10,
        padding: "2rem", textAlign: "center", color: "#9ca3af", fontStyle: "italic",
        marginBottom: "2rem",
      }}>
        No geo-tagged incidents available. Submit a report with GPS to see it here.
      </div>
    );
  }

  // Initial center — first valid point (MapBoundsController will adjust after mount)
  const initialCenter = [points[0].lat, points[0].lng];

  return (
    <div style={{ marginBottom: "2rem" }}>
      <MapContainer
        center={initialCenter}
        zoom={12}
        style={{ height: 420, borderRadius: 10, border: "1px solid #e2e8f0" }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Dynamically fit bounds whenever points change */}
        <MapBoundsController points={points} />

        {points.map(({ lat, lng, incident: inc }) => (
          <CircleMarker
            key={inc.incident_id}
            center={[lat, lng]}
            radius={10}
            pathOptions={{
              color:       SEVERITY_COLORS[inc.risk_level] || "#6b7280",
              fillColor:   SEVERITY_COLORS[inc.risk_level] || "#6b7280",
              fillOpacity: 0.85,
              weight:      2,
            }}
          >
            <Popup>
              <div style={{ fontSize: 13, minWidth: 190 }}>
                <strong>#{inc.incident_id} - {inc.incident_type}</strong><br />
                <span style={{ color: "#6b7280" }}>{inc.location}</span><br />
                <span>Severity: <b>{inc.ai_severity}</b></span><br />
                <span>Status: {inc.status}</span><br />
                <span style={{ fontSize: 11, color: "#9ca3af" }}>
                  {lat.toFixed(5)}, {lng.toFixed(5)}
                </span>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      {/* Legend */}
      <div style={{ display: "flex", gap: "1rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
        {Object.entries(SEVERITY_COLORS).map(([level, color]) => (
          <span key={level} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12 }}>
            <span style={{ width: 12, height: 12, borderRadius: "50%", background: color, display: "inline-block" }} />
            {level}
          </span>
        ))}
        <span style={{ fontSize: 12, color: "#9ca3af", marginLeft: "auto" }}>
          {points.length} location{points.length !== 1 ? "s" : ""} shown
        </span>
      </div>
    </div>
  );
}