import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPublicSummary } from "../api.js";

function fmt(iso) { return iso ? new Date(iso).toLocaleString() : "-"; }
function riskColor(level) {
  return { CRITICAL:"#b91c1c", HIGH:"#c2410c", MEDIUM:"#854d0e", LOW:"#15803d" }[level] || "#6b7280";
}

export default function PublicDashboard() {
  const [data, setData]       = useState(null);
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(true);
  const [loadedAt, setLoadedAt] = useState(null);

  useEffect(() => {
    getPublicSummary()
      .then(d => { setData(d); setLoadedAt(new Date().toLocaleTimeString()); })
      .catch(err => {
        const msg = err.message || "Failed to load public data.";
        if (msg.includes("Failed to fetch")) {
          setError("Cannot reach the server. Make sure the backend is running on port 8000.");
        } else {
          setError(msg);
        }
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="container">
      <Link to="/" className="back-link">Back to Home</Link>
      <div className="result-card">
        <div className="loading-wrap">
          <div className="spinner" />
          <p>Loading public safety data...</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container">
      <Link to="/" className="back-link">Back to Home</Link>
      <div className="result-card">
        <h1>Public Safety Dashboard</h1>
        <p style={{ color: "#6b7280", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
          Anonymized road safety data for citizen transparency. No personal information is shown.
        </p>

        {error && <div className="error"><span>Warning: </span><span>{error}</span></div>}

        {data && data.total_reports === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No incidents reported yet.</p>
            <p style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>
              <Link to="/submit">Submit the first report</Link>
            </p>
          </div>
        )}

        {data && data.total_reports > 0 && (
          <>
            <div className="pub-cards">
              {[
                { label: "Total Reports",   value: data.total_reports },
                { label: "Resolved",        value: data.resolved_reports },
                { label: "Active Hotspots", value: data.active_hotspots },
                { label: "Top Issue",       value: data.top_issue_type || "-", text: true },
              ].map(c => (
                <div key={c.label} className="pub-card">
                  <div className="pc-label">{c.label}</div>
                  <div className={"pc-value" + (c.text ? " text" : "")}>{c.value}</div>
                </div>
              ))}
            </div>

            {data.severity_distribution.length > 0 && (
              <div className="section">
                <h2>Severity Distribution</h2>
                <div className="dist-chips">
                  {data.severity_distribution.map(d => (
                    <div key={d.severity} className="dist-chip">
                      <div className="dc-count" style={{ color: riskColor(d.severity.toUpperCase()) }}>{d.count}</div>
                      <div className="dc-label">{d.severity}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.incident_type_distribution.length > 0 && (
              <div className="section">
                <h2>Incident Type Distribution</h2>
                <div className="dist-chips">
                  {data.incident_type_distribution.map(d => (
                    <div key={d.incident_type} className="dist-chip">
                      <div className="dc-count" style={{ color: "#1e3a5f" }}>{d.count}</div>
                      <div className="dc-label">{d.incident_type.replace("_", " ")}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.hotspots.length > 0 && (
              <div className="section">
                <h2>Active Hotspots</h2>
                {data.hotspots.map(h => (
                  <div key={h.hotspot_id} className="hotspot-row">
                    <div>
                      <div className="hs-name">{h.area_name}</div>
                      <div className="hs-meta">{h.incident_count} incidents - {h.dominant_incident_type.replace("_", " ")}</div>
                    </div>
                    <span className="risk-pill" style={{ background: riskColor(h.risk_level) }}>{h.risk_level}</span>
                  </div>
                ))}
              </div>
            )}

            {data.recent_incidents.length > 0 && (
              <div className="section">
                <h2>Recent Incidents</h2>
                {data.recent_incidents.map(i => (
                  <div key={i.incident_id} className="incident-row">
                    <div>
                      <div className="ir-type">{i.incident_type.replace("_", " ")}</div>
                      <div className="ir-loc">{i.location}</div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "0.2rem" }}>
                      <span className="ir-sev" style={{ color: riskColor(i.risk_level) }}>{i.ai_severity}</span>
                      <span className="ir-time">{fmt(i.created_at)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        <div className="pub-footer">
          {loadedAt && <span>Last updated: {loadedAt}</span>}
          <span style={{ marginLeft: "1rem" }}>No personal information (name, phone) is shown on this page.</span>
        </div>
      </div>
    </div>
  );
}