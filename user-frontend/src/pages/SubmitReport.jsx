import { useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { submitIncident } from "../api.js";

const EMPTY = {
  name: "", phone: "", location: "",
  latitude: "", longitude: "",
  incident_type: "accident",
  description: "", victims_count: 0, image_url: "",
};

const INCIDENT_LABELS = {
  accident:           "Accident",
  pothole:            "Pothole",
  road_block:         "Road Block",
  signal_issue:       "Signal Issue",
  street_light_issue: "Street Light Issue",
  other:              "Other",
};

export default function SubmitReport() {
  const navigate = useNavigate();
  const [form, setForm]             = useState(EMPTY);
  const [error, setError]           = useState("");
  const [gpsStatus, setGpsStatus]   = useState("");
  const [gpsIsError, setGpsIsError] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [touched, setTouched]       = useState({});

  // Keep a ref so validation always reads the latest form state
  const formRef = useRef(form);
  formRef.current = form;

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  }

  function handleBlur(e) {
    setTouched(prev => ({ ...prev, [e.target.name]: true }));
  }

  function captureGPS() {
    if (!navigator.geolocation) {
      setGpsIsError(true);
      setGpsStatus("Geolocation is not supported by your browser.");
      return;
    }

    setGpsLoading(true);
    setGpsIsError(false);
    setGpsStatus("Detecting location...");

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        const latStr = lat.toFixed(6);
        const lngStr = lng.toFixed(6);
        // Build a coordinate string that becomes the location value
        const locationValue = latStr + "," + lngStr;

        setForm(prev => ({
          ...prev,
          location:  locationValue,
          latitude:  latStr,
          longitude: lngStr,
        }));

        // Clear location validation error since we now have a value
        setTouched(prev => ({ ...prev, location: false }));

        setGpsIsError(false);
        setGpsLoading(false);
        setGpsStatus("GPS location captured: " + latStr + ", " + lngStr);
      },
      (err) => {
        setGpsLoading(false);
        setGpsIsError(true);
        if (err.code === 1) {
          setGpsStatus("Location permission denied. Please allow location access or enter manually.");
        } else if (err.code === 2) {
          setGpsStatus("Position unavailable. Please enter location manually.");
        } else if (err.code === 3) {
          setGpsStatus("Location request timed out. Please try again.");
        } else {
          setGpsStatus("Unable to retrieve location. Please enter manually.");
        }
      },
      { timeout: 10000, maximumAge: 0 }
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    // Read from formRef to avoid stale closure issues
    const current = formRef.current;

    if (!current.name.trim())        { setError("Full name is required."); return; }
    if (!current.phone.trim())       { setError("Phone number is required."); return; }
    if (!current.location.trim())    { setError("Location is required. Enter an address or use GPS."); return; }
    if (!current.description.trim()) { setError("Description is required."); return; }
    if (current.description.trim().length < 10) {
      setError("Description must be at least 10 characters."); return;
    }

    setSubmitting(true);

    const payload = {
      name:          current.name.trim(),
      phone:         current.phone.trim(),
      location:      current.location.trim(),
      incident_type: current.incident_type,
      description:   current.description.trim(),
      victims_count: parseInt(current.victims_count, 10) || 0,
    };
    if (current.latitude)  payload.latitude  = parseFloat(current.latitude);
    if (current.longitude) payload.longitude = parseFloat(current.longitude);
    if (current.image_url && current.image_url.trim()) {
      payload.image_url = current.image_url.trim();
    }

    try {
      const result = await submitIncident(payload);
      navigate("/result/" + result.incident_id);
    } catch (err) {
      const msg = err.message || "Submission failed. Please try again.";
      if (msg.includes("422") || msg.includes("validation")) {
        setError("Some fields are invalid. Please check your input and try again.");
      } else if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setError("Cannot reach the server. Make sure the backend is running on port 8000.");
      } else {
        setError(msg);
      }
      setSubmitting(false);
    }
  }

  const descLen = form.description.length;
  const locationMissing = touched.location && !form.location.trim();

  return (
    <div className="container">
      <Link to="/" className="back-link">Back to Home</Link>
      <div className="form-card">
        <h1>Submit Road Report</h1>
        <p className="form-subtitle">Report a road hazard - our AI will assess the risk instantly.</p>

        {error && (
          <div className="error">
            <span>Warning: </span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>

          {/* Full Name */}
          <div className="form-group">
            <label htmlFor="name">Full Name <span className="required">*</span></label>
            <input
              id="name" name="name" type="text"
              value={form.name} onChange={handleChange} onBlur={handleBlur}
              className={touched.name && !form.name.trim() ? "invalid" : ""}
              placeholder="e.g. Ravi Kumar"
              autoComplete="name"
            />
            {touched.name && !form.name.trim() && (
              <span className="field-hint" style={{ color: "#dc2626" }}>Name is required</span>
            )}
          </div>

          {/* Phone */}
          <div className="form-group">
            <label htmlFor="phone">Phone Number <span className="required">*</span></label>
            <input
              id="phone" name="phone" type="tel"
              value={form.phone} onChange={handleChange} onBlur={handleBlur}
              className={touched.phone && !form.phone.trim() ? "invalid" : ""}
              placeholder="+91 98765 43210"
              autoComplete="tel"
            />
          </div>

          {/* Location + GPS */}
          <div className="form-group">
            <label htmlFor="location">Location <span className="required">*</span></label>
            <div className="gps-row">
              <input
                id="location" name="location" type="text"
                value={form.location}
                onChange={handleChange}
                onBlur={handleBlur}
                className={locationMissing ? "invalid" : ""}
                placeholder="e.g. Avinashi Road, Coimbatore — or use GPS"
              />
              <button
                type="button"
                className="btn btn-outline btn-sm"
                onClick={captureGPS}
                disabled={gpsLoading}
              >
                {gpsLoading ? "Detecting..." : "Use GPS"}
              </button>
            </div>

            {/* GPS status message */}
            {gpsStatus && (
              <p className={"gps-coords" + (gpsIsError ? " error-text" : "")}>
                {gpsStatus}
              </p>
            )}

            {/* Inline validation error */}
            {locationMissing && (
              <span className="field-hint" style={{ color: "#dc2626" }}>
                Location is required. Enter an address or use GPS.
              </span>
            )}

            {!gpsStatus && (
              <span className="field-hint">Type an address or click "Use GPS" to auto-fill</span>
            )}
          </div>

          {/* Incident Type */}
          <div className="form-group">
            <label htmlFor="incident_type">Incident Type <span className="required">*</span></label>
            <select id="incident_type" name="incident_type" value={form.incident_type} onChange={handleChange}>
              {Object.entries(INCIDENT_LABELS).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div className="form-group">
            <label htmlFor="description">Description <span className="required">*</span></label>
            <textarea
              id="description" name="description"
              value={form.description} onChange={handleChange} onBlur={handleBlur}
              className={touched.description && form.description.trim().length < 10 ? "invalid" : ""}
              placeholder="Describe the incident clearly - include details like injuries, road conditions, vehicles involved..."
            />
            <span className={"char-count" + (descLen > 400 ? " warn" : "")}>
              {descLen} characters {descLen < 10 && descLen > 0 ? "(min 10)" : ""}
            </span>
            <span className="field-hint">More detail = better AI assessment</span>
          </div>

          {/* Victims Count */}
          <div className="form-group">
            <label htmlFor="victims_count">Victims Count <span className="optional">(optional)</span></label>
            <input
              id="victims_count" name="victims_count" type="number"
              min="0" max="100" value={form.victims_count} onChange={handleChange}
            />
            <span className="field-hint">Number of people injured or affected</span>
          </div>

          {/* Image URL */}
          <div className="form-group">
            <label htmlFor="image_url">Image URL <span className="optional">(optional)</span></label>
            <input
              id="image_url" name="image_url" type="url"
              value={form.image_url} onChange={handleChange}
              placeholder="https://example.com/photo.jpg"
            />
          </div>

          <div className="submit-row">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Report"}
            </button>
            {!submitting && (
              <span className="submit-note">AI result shown instantly after submit</span>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}