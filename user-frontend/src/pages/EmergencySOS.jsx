import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const CONTACTS = [
  { name: 'Ambulance',        phone: '108' },
  { name: 'Police',           phone: '100' },
  { name: 'Fire Brigade',     phone: '101' },
  { name: 'Disaster Mgmt',    phone: '1077' },
  { name: 'Women Helpline',   phone: '1091' },
  { name: 'Road Accident',    phone: '1073' },
];

const MOCK_SERVICES = [
  { name: 'City General Hospital',   type: 'Hospital',  phone: '044-2345-6789', distance: '1.2 km' },
  { name: 'Central Police Station',  type: 'Police',    phone: '100',           distance: '0.8 km' },
  { name: 'National Ambulance Svc',  type: 'Ambulance', phone: '108',           distance: '1.0 km' },
  { name: 'Road Rescue Team Alpha',  type: 'Rescue',    phone: '044-2600-9999', distance: '2.0 km' },
];

export default function EmergencySOS() {
  const [coords, setCoords]     = useState(null);
  const [gpsError, setGpsError] = useState('');
  const [summary, setSummary]   = useState('');

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => setCoords({ lat: pos.coords.latitude.toFixed(5), lng: pos.coords.longitude.toFixed(5) }),
        ()   => setGpsError('Location unavailable — showing default services.')
      );
    }
  }, []);

  function generateSummary() {
    const loc = coords ? `Lat: ${coords.lat}, Lng: ${coords.lng}` : 'Location not available';
    const text = [
      '=== PATHSHIELD AI — EMERGENCY SUMMARY ===',
      `Time: ${new Date().toLocaleString()}`,
      `Location: ${loc}`,
      '',
      'NEAREST SERVICES:',
      ...MOCK_SERVICES.map(s => `  • ${s.type}: ${s.name} — ${s.distance} — ${s.phone}`),
      '',
      'SUGGESTED ACTIONS:',
      '  1. Call 108 (Ambulance) immediately if injuries are present.',
      '  2. Call 100 (Police) to secure the scene.',
      '  3. Do not move injured persons unless in immediate danger.',
      '  4. Keep the area clear for emergency vehicles.',
    ].join('\n');
    setSummary(text);
  }

  return (
    <div className="sos-page">
      <Link to="/" className="back-link" style={{ color: '#9ca3af', alignSelf: 'flex-start' }}>← Back</Link>
      <h1>🆘 Emergency SOS</h1>
      <p className="sos-sub">One-click emergency help — stay calm, help is on the way.</p>

      {gpsError && <p style={{ color: '#f87171', marginBottom: '1rem', fontSize: '0.9rem' }}>{gpsError}</p>}
      {coords && (
        <p style={{ color: '#34d399', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
          📍 Your location: {coords.lat}, {coords.lng}
        </p>
      )}

      {/* Emergency contacts */}
      <div className="sos-card" style={{ width: '100%', maxWidth: '600px' }}>
        <h2>Emergency Contacts</h2>
        {CONTACTS.map(c => (
          <div key={c.phone} className="sos-contact">
            <span className="sc-name">{c.name}</span>
            <a href={`tel:${c.phone}`} className="sc-phone">{c.phone}</a>
          </div>
        ))}
      </div>

      {/* Nearest services */}
      <div className="sos-card" style={{ width: '100%', maxWidth: '600px' }}>
        <h2>Nearest Services</h2>
        {MOCK_SERVICES.map(s => (
          <div key={s.name} className="sos-contact">
            <span className="sc-name">{s.type}: {s.name} ({s.distance})</span>
            <a href={`tel:${s.phone}`} className="sc-phone">{s.phone}</a>
          </div>
        ))}
      </div>

      {/* Generate summary */}
      <button className="btn btn-danger" style={{ marginBottom: '1.5rem', minWidth: '260px' }} onClick={generateSummary}>
        📋 Generate Emergency Summary
      </button>

      {summary && (
        <div className="sos-card" style={{ width: '100%', maxWidth: '600px' }}>
          <h2>Emergency Summary</h2>
          <div className="sos-summary">{summary}</div>
        </div>
      )}
    </div>
  );
}
