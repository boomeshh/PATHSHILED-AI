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

export const submitIncident  = (data) =>
  request('/incident/report', { method: 'POST', body: JSON.stringify(data) });

export const getIncident     = (id) => request(`/incident/${id}`);
export const getPublicSummary = ()  => request('/public/summary');
