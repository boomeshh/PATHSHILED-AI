# PathShield AI — Phase 2

> **Protecting every journey with AI**

A hackathon-ready road safety incident reporting platform with AI-powered risk scoring, GPS capture, emergency services, and a full admin dashboard.

---

## Folder Structure

```
pathshield-ai/
├── backend/              FastAPI backend + AI engine
│   ├── main.py           App entry point, all routes
│   ├── ai_engine.py      Rule-based AI scoring engine
│   ├── mock_services.py  Mock emergency services data
│   ├── database.py       SQLAlchemy + SQLite setup
│   ├── models.py         ORM models
│   ├── schemas.py        Pydantic schemas
│   ├── requirements.txt
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       └── test_ai_engine.py
├── user-frontend/        React app for public users (port 5173)
│   ├── src/
│   │   ├── pages/Home.jsx
│   │   ├── pages/SubmitReport.jsx
│   │   ├── pages/AIResult.jsx
│   │   └── pages/EmergencySOS.jsx
│   ├── .env.example
│   └── vite.config.js
├── admin-frontend/       React app for admins (port 5174)
│   ├── src/
│   │   └── pages/Dashboard.jsx
│   ├── .env.example
│   └── vite.config.js
└── README.md
```

---

## Backend Setup

```bash
cd backend
py -m venv venv
venv\Scripts\activate
py -m pip install -r requirements.txt
pytest
uvicorn main:app --reload
```

API runs at: http://127.0.0.1:8000

---

## User Frontend Setup

```bash
cd user-frontend
npm install
cp .env.example .env
npm run dev
```

Runs at: http://localhost:5173

---

## Admin Frontend Setup

```bash
cd admin-frontend
npm install
cp .env.example .env
npm run dev -- --port 5174
```

Runs at: http://localhost:5174

---

## Test Commands

```bash
# Backend tests (from backend/)
pytest tests/test_api.py tests/test_ai_engine.py -v

# Frontend build verification
cd user-frontend  && npm run build
cd admin-frontend && npm run build
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/incident/report` | Submit incident, get AI result |
| GET | `/incident/all` | List all incidents |
| GET | `/incident/{id}` | Get single incident |
| PATCH | `/incident/{id}/status` | Update status (reported/in_progress/resolved) |
| GET | `/analytics/summary` | Aggregate stats + distributions |

### POST /incident/report — Request Body

```json
{
  "name": "Jane Doe",
  "phone": "9876543210",
  "location": "MG Road, Bangalore",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "incident_type": "accident",
  "description": "Bike accident with head injury",
  "victims_count": 2,
  "image_url": null
}
```

---

## Demo Flow

1. Open **user-frontend** → Home page
2. Click **Submit Road Report** → fill form, use GPS button
3. Submit → redirected to **AI Result** page showing score, reasons, nearby services
4. Click **Emergency SOS** from home → see contacts, generate summary
5. Open **admin-frontend** → Dashboard with all incidents
6. Filter by severity/status, click **View** for full details
7. Click **In Progress** / **Resolve** to update status
8. Scroll down for analytics distribution tables

---

## Hackathon Notes

- No external AI APIs — fully offline rule-based engine
- No auth required — MVP scope
- SQLite database — zero setup, file-based persistence
- All emergency services are mock data (clearly labeled)
- CORS configured for both frontend ports (5173 + 5174)
- Emergency numbers: **108** (Ambulance), **100** (Police)
