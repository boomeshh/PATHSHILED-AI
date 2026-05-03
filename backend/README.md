# PathShield AI — Backend

FastAPI backend with SQLite database and AI-powered risk scoring.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Run tests

All tests:

```bash
pytest tests/ -v
```

Property-based tests only:

```bash
pytest tests/test_properties.py -v
```
