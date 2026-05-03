import { useEffect, useState, useCallback } from 'react';
import {
  getAllIncidents, getAnalytics, getHotspots,
  updateStatus, assignIncident, getTimeline,
  seedDemo, clearDemo, exportCsvUrl,
} from '../api.js';
import IncidentMap from '../components/IncidentMap.jsx';

// ---- Helpers ----------------------------------------------------------------

function badgeRisk(level) {
  const m = { LOW:'badge-low', MEDIUM:'badge-medium', HIGH:'badge-high', CRITICAL:'badge-critical' };
  return `badge ${m[level]||''}`;
}
function badgeStatus(s) {
  const m = { reported:'badge-reported', in_progress:'badge-in_progress',
              resolved:'badge-resolved', assigned:'badge-assigned', verified:'badge-verified' };
  return `badge ${m[s]||''}`;
}
function fmt(iso) { return iso ? new Date(iso).toLocaleString() : '—'; }
function maxCount(arr) { return Math.max(...arr.map(d => d.count), 1); }

// ---- Timeline ---------------------------------------------------------------

function TimelinePanel({ incidentId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTimeline(incidentId)
      .then(setEvents)
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [incidentId]);

  if (loading) return <p className="loading">Loading timeline…</p>;
  if (!events.length) return <p style={{ color: '#9ca3af', fontSize: '0.85rem' }}>No events yet.</p>;

  return (
    <div className="timeline">
      {events.map((e, i) => (
        <div key={i} className="tl-event">
          <div className="tl-dot" />
          <div className="tl-body">
            <div className="tl-action">{e.action}</div>
            <div className="tl-meta">{e.actor} · {fmt(e.timestamp)}</div>
            {e.note && <div className="tl-note">{e.note}</div>}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---- Assign Panel -----------------------------------------------------------

const DEPARTMENTS = ['Police','Ambulance','Road Maintenance','Traffic Department','Vehicle Rescue'];

function AssignPanel({ incident, onAssigned }) {
  const [dept, setDept]   = useState(incident.assigned_department || DEPARTMENTS[0]);
  const [to, setTo]       = useState(incident.assigned_to || '');
  const [busy, setBusy]   = useState(false);
  const [err, setErr]     = useState('');

  async function handleAssign() {
    if (!to.trim()) { setErr('Please enter assignee name.'); return; }
    setBusy(true); setErr('');
    try {
      const updated = await assignIncident(incident.incident_id, dept, to);
      onAssigned(updated);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  }

  return (
    <div style={{ marginTop: '0.75rem' }}>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 2 }}>Department</label>
          <select value={dept} onChange={e => setDept(e.target.value)}
            style={{ padding: '0.35rem 0.6rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem' }}>
            {DEPARTMENTS.map(d => <option key={d}>{d}</option>)}
          </select>
        </div>
        <div>
          <label style={{ fontSize: '0.75rem', fontWeight: 700, color: '#6b7280', display: 'block', marginBottom: 2 }}>Assign To</label>
          <input value={to} onChange={e => setTo(e.target.value)}
            placeholder="Inspector / Team name"
            style={{ padding: '0.35rem 0.6rem', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem', minWidth: 160 }} />
        </div>
        <button className="btn btn-primary btn-sm" onClick={handleAssign} disabled={busy}>
          {busy ? 'Assigning…' : 'Assign'}
        </button>
      </div>
      {err && <p style={{ color: '#b91c1c', fontSize: '0.8rem', marginTop: 4 }}>{err}</p>}
    </div>
  );
}

// ---- AI Breakdown -----------------------------------------------------------

function BreakdownTable({ breakdown }) {
  if (!breakdown || !breakdown.length) return null;
  return (
    <table className="dist-table" style={{ marginTop: '0.5rem' }}>
      <thead><tr><th>Factor</th><th>Points</th><th>Reason</th></tr></thead>
      <tbody>
        {breakdown.map((b, i) => (
          <tr key={i}>
            <td>{b.factor}</td>
            <td><strong>+{b.points}</strong></td>
            <td style={{ color: '#6b7280' }}>{b.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ---- Detail Modal -----------------------------------------------------------

function DetailModal({ incident, onClose, onUpdated }) {
  if (!incident) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        <h2>Incident #{incident.incident_id} — {incident.incident_type}</h2>

        <div className="detail-row"><span className="detail-label">Name</span><span className="detail-value">{incident.name}</span></div>
        <div className="detail-row"><span className="detail-label">Phone</span><span className="detail-value">{incident.phone}</span></div>
        <div className="detail-row"><span className="detail-label">Location</span><span className="detail-value">{incident.location}</span></div>
        {incident.latitude != null && (
          <div className="detail-row">
            <span className="detail-label">Coordinates</span>
            <span className="detail-value">{incident.latitude}, {incident.longitude}</span>
          </div>
        )}
        <div className="detail-row"><span className="detail-label">Victims</span><span className="detail-value">{incident.victims_count}</span></div>
        <div className="detail-row"><span className="detail-label">Status</span><span className="detail-value"><span className={badgeStatus(incident.status)}>{incident.status}</span></span></div>
        <div className="detail-row"><span className="detail-label">AI Severity</span><span className="detail-value">{incident.ai_severity}</span></div>
        <div className="detail-row"><span className="detail-label">Risk Level</span><span className="detail-value"><span className={badgeRisk(incident.risk_level)}>{incident.risk_level}</span></span></div>
        <div className="detail-row"><span className="detail-label">AI Score</span><span className="detail-value">{incident.ai_score}/100</span></div>
        <div className="detail-row"><span className="detail-label">Trust Score</span><span className="detail-value">{incident.trust_score}/100</span></div>
        <div className="detail-row"><span className="detail-label">Duplicate?</span><span className="detail-value">{incident.duplicate_possible ? `⚠️ Yes (of #${incident.duplicate_of})` : '✅ Unique'}</span></div>
        {incident.image_url && (
          <div className="detail-row">
            <span className="detail-label">Image</span>
            <span className="detail-value"><a href={incident.image_url} target="_blank" rel="noopener noreferrer">View Image</a></span>
          </div>
        )}

        <div className="section-title">Description</div>
        <p style={{ fontSize: '0.875rem', color: '#374151', marginBottom: '0.5rem' }}>{incident.description}</p>

        <div className="section-title">Why AI gave this score?</div>
        <BreakdownTable breakdown={incident.explanation_breakdown} />

        <div className="section-title">AI Reasons</div>
        <ul className="list-bullets">
          {(incident.ai_reasons || []).map((r, i) => <li key={i}>{r}</li>)}
        </ul>

        <div className="section-title">First Aid Guidance</div>
        <ul className="list-bullets">
          {(incident.first_aid || []).map((f, i) => <li key={i}>{f}</li>)}
        </ul>

        <div className="section-title">Nearby Services</div>
        <div className="services-grid">
          {[...(incident.nearby_hospitals||[]),...(incident.nearby_police||[]),...(incident.ambulance_contact||[])].map((s,i)=>(
            <div key={i} className="svc-card">
              <div className="svc-name">{s.name}</div>
              <div className="svc-dist">{s.distance}</div>
              <div className="svc-phone">{s.phone}</div>
            </div>
          ))}
        </div>

        <div className="section-title">Assign to Department</div>
        <AssignPanel incident={incident} onAssigned={updated => { onUpdated(updated); }} />

        <div className="section-title">Timeline</div>
        <TimelinePanel incidentId={incident.incident_id} />
      </div>
    </div>
  );
}

// ---- Hotspot Table ----------------------------------------------------------

function HotspotTable({ hotspots }) {
  if (!hotspots || !hotspots.length) return (
    <p className="empty">No hotspots detected yet. Need 3+ incidents in same area.</p>
  );
  return (
    <div className="table-wrapper" style={{ marginBottom: '1.5rem' }}>
      <table>
        <thead><tr><th>Area</th><th>Count</th><th>Dominant Type</th><th>Risk Level</th></tr></thead>
        <tbody>
          {hotspots.map(h => (
            <tr key={h.hotspot_id}>
              <td>{h.area_name}</td>
              <td><strong>{h.incident_count}</strong></td>
              <td>{h.dominant_incident_type}</td>
              <td><span className={badgeRisk(h.risk_level)}>{h.risk_level}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---- Analytics Section ------------------------------------------------------

function AnalyticsSection({ analytics }) {
  if (!analytics) return null;
  const sevMax  = maxCount(analytics.severity_distribution);
  const typeMax = maxCount(analytics.incident_type_distribution);
  const sevColor = { Critical:'critical', High:'high', Moderate:'moderate', Low:'low' };

  return (
    <div className="analytics-section">
      <h2>Analytics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <div>
          <p style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.875rem' }}>Severity Distribution</p>
          <table className="dist-table">
            <thead><tr><th>Severity</th><th>Count</th><th style={{ width: 120 }}>Bar</th></tr></thead>
            <tbody>
              {analytics.severity_distribution.length === 0
                ? <tr><td colSpan={3} className="empty">No data</td></tr>
                : analytics.severity_distribution.map(d => (
                  <tr key={d.severity}>
                    <td>{d.severity}</td><td>{d.count}</td>
                    <td><div className="bar-wrap"><div className={`bar ${sevColor[d.severity]||''}`} style={{ width: `${(d.count/sevMax)*100}px` }} /></div></td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
        <div>
          <p style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.875rem' }}>Incident Type Distribution</p>
          <table className="dist-table">
            <thead><tr><th>Type</th><th>Count</th><th style={{ width: 120 }}>Bar</th></tr></thead>
            <tbody>
              {analytics.incident_type_distribution.length === 0
                ? <tr><td colSpan={3} className="empty">No data</td></tr>
                : analytics.incident_type_distribution.map(d => (
                  <tr key={d.incident_type}>
                    <td>{d.incident_type}</td><td>{d.count}</td>
                    <td><div className="bar-wrap"><div className="bar" style={{ width: `${(d.count/typeMax)*100}px` }} /></div></td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ---- Main Dashboard ---------------------------------------------------------

export default function Dashboard() {
  const [incidents, setIncidents] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [hotspots,  setHotspots]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState('');
  const [selected,  setSelected]  = useState(null);
  const [demoMsg,   setDemoMsg]   = useState('');
  const [demoBusy,  setDemoBusy]  = useState(false);

  const [search,         setSearch]         = useState('');
  const [filterStatus,   setFilterStatus]   = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [updating,       setUpdating]       = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [inc, ana, hs] = await Promise.all([getAllIncidents(), getAnalytics(), getHotspots()]);
      setIncidents(inc); setAnalytics(ana); setHotspots(hs); setError('');
    } catch (err) {
      setError(err.message || 'Failed to load data.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleStatusUpdate(id, status) {
    setUpdating(p => ({ ...p, [id]: true }));
    try {
      const updated = await updateStatus(id, status);
      setIncidents(p => p.map(i => i.incident_id === id ? updated : i));
      if (selected?.incident_id === id) setSelected(updated);
    } catch (err) { setError(err.message); }
    finally { setUpdating(p => ({ ...p, [id]: false })); }
  }

  function handleUpdated(updated) {
    setIncidents(p => p.map(i => i.incident_id === updated.incident_id ? updated : i));
    setSelected(updated);
  }

  async function handleSeedDemo() {
    setDemoBusy(true); setDemoMsg('');
    try {
      const r = await seedDemo();
      setDemoMsg(`✅ ${r.message}`);
      await load();
    } catch (e) { setDemoMsg(`❌ ${e.message}`); }
    finally { setDemoBusy(false); }
  }

  async function handleClearDemo() {
    setDemoBusy(true); setDemoMsg('');
    try {
      const r = await clearDemo();
      setDemoMsg(`🗑️ ${r.message}`);
      await load();
    } catch (e) { setDemoMsg(`❌ ${e.message}`); }
    finally { setDemoBusy(false); }
  }

  const filtered = incidents.filter(i => {
    const q = search.toLowerCase();
    const ms = !q || [i.name, i.location, i.incident_type, i.phone].some(f => (f||'').toLowerCase().includes(q));
    return ms && (!filterStatus || i.status === filterStatus) && (!filterSeverity || i.ai_severity === filterSeverity);
  });

  const highRisk = incidents.filter(i => i.risk_level === 'CRITICAL' || i.risk_level === 'HIGH').slice(0, 5);

  if (loading) return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">🛡️ PathShield</div>
      </aside>
      <main className="main">
        <div className="loading-full">
          <div className="spinner" />
          <p>Loading Road Safety Command Center…</p>
        </div>
      </main>
    </div>
  );

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-logo">🛡️ PathShield</div>
        <span className="sidebar-link active">📊 Dashboard</span>
        <span className="sidebar-version">v3.0 Command Center</span>
      </aside>

      <main className="main">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem' }}>
          <h1 className="page-title" style={{ margin: 0 }}>Road Safety Command Center</h1>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm" onClick={handleSeedDemo} disabled={demoBusy}>
              {demoBusy ? '…' : '🌱 Load Demo Data'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={handleClearDemo} disabled={demoBusy}>
              🗑️ Clear Demo
            </button>
            <a href={exportCsvUrl()} className="btn btn-ghost btn-sm" download>
              📥 Export CSV
            </a>
            <button className="btn btn-ghost btn-sm" onClick={load}>↻ Refresh</button>
          </div>
        </div>

        {error   && <p className="error">{error}</p>}
        {demoMsg && <p className="success-msg">{demoMsg}</p>}

        {/* Demo walkthrough banner — shown when no data */}
        {!loading && incidents.length === 0 && (
          <div className="demo-banner">
            <div>
              <div className="db-title">👋 Welcome to PathShield AI Command Center</div>
              <div className="db-text">No incidents yet. Load demo data to see the full dashboard in action.</div>
            </div>
            <div className="db-actions">
              <button className="btn btn-primary btn-sm" onClick={handleSeedDemo} disabled={demoBusy}>
                {demoBusy ? '…' : '🌱 Load Demo Data'}
              </button>
            </div>
          </div>
        )}

        {/* Overview cards */}
        {analytics && (
          <div className="cards-row">
            <div className="stat-card"><div className="sc-label">Total Reports</div><div className="sc-value">{analytics.total_reports}</div></div>
            <div className="stat-card critical"><div className="sc-label">Critical</div><div className="sc-value">{analytics.critical_reports}</div></div>
            <div className="stat-card high"><div className="sc-label">High Risk</div><div className="sc-value">{analytics.high_risk_reports}</div></div>
            <div className="stat-card resolved"><div className="sc-label">Resolved</div><div className="sc-value">{analytics.resolved_reports}</div></div>
            <div className="stat-card"><div className="sc-label">Active Hotspots</div><div className="sc-value" style={{ color: '#dc2626' }}>{analytics.active_hotspots}</div></div>
            <div className="stat-card"><div className="sc-label">Top Incident</div><div className="sc-value" style={{ fontSize: '1rem', paddingTop: '0.4rem' }}>{analytics.top_incident_type || '—'}</div></div>
          </div>
        )}

        {/* Map */}
        <div className="analytics-section">
          <h2>Incident Map</h2>
          <IncidentMap incidents={incidents} />
        </div>

        {/* Hotspots */}
        <div className="analytics-section">
          <h2>🔥 Hotspot Detection</h2>
          <HotspotTable hotspots={hotspots} />
        </div>

        {/* Filters */}
        <div className="filters-row">
          <input type="text" placeholder="Search name / location / type…"
            value={search} onChange={e => setSearch(e.target.value)} />
          <select value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
            <option value="">All Statuses</option>
            <option value="reported">Reported</option>
            <option value="verified">Verified</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
          </select>
          <select value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}>
            <option value="">All Severities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Moderate">Moderate</option>
            <option value="Low">Low</option>
          </select>
          {(search || filterStatus || filterSeverity) && (
            <span className="filter-count">
              {filtered.length} of {incidents.length} shown
              <button
                className="btn btn-ghost btn-sm"
                style={{ marginLeft: '0.5rem', padding: '0.2rem 0.5rem' }}
                onClick={() => { setSearch(''); setFilterStatus(''); setFilterSeverity(''); }}
              >✕ Clear</button>
            </span>
          )}
        </div>

        {/* Reports table */}
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Phone</th><th>Location</th><th>Type</th>
                <th>Severity</th><th>Risk</th><th>Score</th><th>Trust</th>
                <th>Dup?</th><th>Status</th><th>Created</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0
                ? <tr><td colSpan={13} className="empty">No incidents found.</td></tr>
                : filtered.map(i => (
                  <tr key={i.incident_id}>
                    <td>{i.incident_id}</td>
                    <td>{i.name}</td>
                    <td>{i.phone}</td>
                    <td>{i.location}</td>
                    <td>{i.incident_type}</td>
                    <td>{i.ai_severity}</td>
                    <td><span className={badgeRisk(i.risk_level)}>{i.risk_level}</span></td>
                    <td>{i.ai_score}</td>
                    <td>{i.trust_score}</td>
                    <td>{i.duplicate_possible ? <span className="badge badge-high">Dup</span> : <span className="badge badge-low">Unique</span>}</td>
                    <td><span className={badgeStatus(i.status)}>{i.status}</span></td>
                    <td style={{ whiteSpace: 'nowrap' }}>{fmt(i.created_at)}</td>
                    <td>
                      <div className="btn-actions">
                        <button className="btn btn-ghost btn-sm" onClick={() => setSelected(i)}>View</button>
                        {i.status !== 'in_progress' && i.status !== 'resolved' && (
                          <button className="btn btn-warning btn-sm" disabled={updating[i.incident_id]}
                            onClick={() => handleStatusUpdate(i.incident_id, 'in_progress')}>In Progress</button>
                        )}
                        {i.status !== 'resolved' && (
                          <button className="btn btn-success btn-sm" disabled={updating[i.incident_id]}
                            onClick={() => handleStatusUpdate(i.incident_id, 'resolved')}>Resolve</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        </div>

        {/* Recent high-risk */}
        {highRisk.length > 0 && (
          <div className="analytics-section">
            <h2>Recent High-Risk Incidents</h2>
            <div className="table-wrapper">
              <table>
                <thead><tr><th>ID</th><th>Type</th><th>Location</th><th>Severity</th><th>Score</th><th>Status</th></tr></thead>
                <tbody>
                  {highRisk.map(i => (
                    <tr key={i.incident_id} style={{ cursor: 'pointer' }} onClick={() => setSelected(i)}>
                      <td>{i.incident_id}</td><td>{i.incident_type}</td><td>{i.location}</td>
                      <td>{i.ai_severity}</td><td>{i.ai_score}</td>
                      <td><span className={badgeStatus(i.status)}>{i.status}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <AnalyticsSection analytics={analytics} />
      </main>

      {selected && (
        <DetailModal
          incident={selected}
          onClose={() => setSelected(null)}
          onUpdated={handleUpdated}
        />
      )}
    </div>
  );
}
