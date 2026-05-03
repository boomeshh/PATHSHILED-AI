const BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const getAllIncidents  = ()           => request('/incident/all');
export const getIncident      = (id)         => request(`/incident/${id}`);
export const updateStatus     = (id, status) =>
  request(`/incident/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) });
export const assignIncident   = (id, dept, to) =>
  request(`/incident/${id}/assign`, { method: 'PATCH',
    body: JSON.stringify({ assigned_department: dept, assigned_to: to }) });
export const getTimeline      = (id)         => request(`/incident/${id}/timeline`);
export const getAnalytics     = ()           => request('/analytics/summary');
export const getHotspots      = ()           => request('/analytics/hotspots');
export const seedDemo         = ()           =>
  request('/demo/seed', { method: 'POST' });
export const clearDemo        = ()           =>
  fetch(`${BASE}/demo/clear`, { method: 'DELETE' }).then(r => r.json());
export const exportCsvUrl     = ()           => `${BASE}/export/incidents.csv`;
