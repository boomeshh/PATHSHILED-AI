import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getIncident } from "../api.js";

function riskClass(level) {
  return { CRITICAL:"critical", HIGH:"high", MEDIUM:"moderate", LOW:"low" }[level] || "low";
}
function riskColor(level) {
  return { CRITICAL:"#b91c1c", HIGH:"#c2410c", MEDIUM:"#854d0e", LOW:"#15803d" }[level] || "#6b7280";
}

function BreakdownTable({ breakdown }) {
  if (!breakdown || !breakdown.length) return null;
  return (
    <table className="breakdown-table">
      <thead><tr><th>Factor</th><th>Points</th><th>Reason</th></tr></thead>
      <tbody>
        {breakdown.map((b, i) => (
          <tr key={i}>
            <td>{b.factor}</td>
            <td className="pts">+{b.points}</td>
            <td>{b.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function AIResult() {
  const { id } = useParams();
  const [data, setData]       = useState(null);
  const [error, setError]     = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getIncident(id)
      .then(setData)
      .catch(err => {
        const msg = err.message || "Failed to load result.";
        if (msg.includes("404") || msg.includes("not found")) {
          setError("Incident #" + id + " not found.");
        } else if (msg.includes("Failed to fetch")) {
          setError("Cannot reach the server. Make sure the backend is running.");
        } else {
          setError(msg);
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return (
    <div className="container">
      <Link to="/" className="back-link">Back to Home</Link>
      <div className="result-card">
        <div className="loading-wrap">
          <div className="spinner" />
          <p>Fetching AI assessment...</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="container">
      <Link to="/" className="back-link">Back to Home</Link>
      {error && <div className="error"><span>Warning: </span><span>{error}</span></div>}
      {data && (
        <div className="result-card">
          <h1>AI Risk Assessment - Incident #{data.incident_id}</h1>
          {data.duplicate_possible && (
            <div className="dup-warning">
              <span>Warning: </span>
              <span>Possible duplicate detected - similar {data.incident_type} report (#{data.duplicate_of}) already exists at this location.</span>
            </div>
          )}
          <div className={"risk-banner " + riskClass(data.risk_level)}>
            <div className="risk-score-big">{data.ai_score}</div>
            <div className="risk-meta">
              <div className="risk-level" style={{ color: riskColor(data.risk_level) }}>{data.risk_level}</div>
              <div className="risk-severity">AI Severity: {data.ai_severity}</div>
              <div className="trust-badge">Trust Score: {data.trust_score}/100</div>
            </div>
          </div>
          {data.explanation_breakdown && data.explanation_breakdown.length > 0 && (
            <div className="section">
              <h2>Why AI gave this score?</h2>
              <BreakdownTable breakdown={data.explanation_breakdown} />
            </div>
          )}
          <div className="section">
            <h2>AI Reasons</h2>
            <ul className="reasons-list">
              {data.ai_reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
          <div className="section">
            <h2>First Aid Guidance</h2>
            <ul className="first-aid-list">
              {data.first_aid.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
          </div>
          <div className="section">
            <h2>Emergency Numbers</h2>
            <div className="emergency-nums">
              <a href="tel:108" className="enum-badge">Ambulance: 108</a>
              <a href="tel:100" className="enum-badge" style={{ background: "#1d4ed8" }}>Police: 100</a>
              <a href="tel:101" className="enum-badge" style={{ background: "#c2410c" }}>Fire: 101</a>
            </div>
          </div>
          {data.nearby_hospitals.length > 0 && (
            <div className="section">
              <h2>Nearby Hospitals</h2>
              <div className="services-grid">
                {data.nearby_hospitals.map((h, i) => (
                  <div key={i} className="service-card">
                    <div className="svc-name">{h.name}</div>
                    <div className="svc-dist">{h.distance}</div>
                    <div className="svc-phone"><a href={"tel:" + h.phone}>{h.phone}</a></div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {data.nearby_police.length > 0 && (
            <div className="section">
              <h2>Nearby Police Station</h2>
              <div className="services-grid">
                {data.nearby_police.map((p, i) => (
                  <div key={i} className="service-card">
                    <div className="svc-name">{p.name}</div>
                    <div className="svc-dist">{p.distance}</div>
                    <div className="svc-phone"><a href={"tel:" + p.phone}>{p.phone}</a></div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {data.ambulance_contact.length > 0 && (
            <div className="section">
              <h2>Ambulance Contact</h2>
              <div className="services-grid">
                {data.ambulance_contact.map((a, i) => (
                  <div key={i} className="service-card">
                    <div className="svc-name">{a.name}</div>
                    <div className="svc-dist">{a.distance}</div>
                    <div className="svc-phone"><a href={"tel:" + a.phone}>{a.phone}</a></div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="result-actions">
            <Link to="/submit" className="btn btn-primary btn-sm">+ Submit Another Report</Link>
            <Link to="/public-dashboard" className="btn btn-secondary btn-sm">View Public Dashboard</Link>
            <button className="btn btn-secondary btn-sm" onClick={() => window.print()}>Print</button>
          </div>
        </div>
      )}
    </div>
  );
}