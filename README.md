# Market Intelligence & Outreach Automation Agent

An end-to-end project that turns a company name and category description into a structured market intelligence report, decision-maker shortlist, verification-first contact intelligence, personalized outreach drafts, and outreach tracking logic.

## Features

- 10-section market intelligence report
- Live workflow visualization with node states
- FastAPI backend with REST and WebSocket endpoints
- React Flow frontend dashboard
- SQLite persistence for runs and tracking events
- Mock mode for reliable demos without external API access
- Live mode for best-effort provider-backed research and enrichment
- Verification-first contact policy: missing or unverified fields stay `not_found`

## Project Structure

```text
market-intelligence-agent/
+-- backend/
|   +-- agents/
|   +-- config.py
|   +-- db.py
|   +-- graph.py
|   +-- main.py
|   +-- services.py
|   +-- state.py
+-- frontend/
|   +-- src/
|   +-- package.json
|   +-- vite.config.js
+-- outputs/
+-- scripts/
|   +-- smoke_test.py
+-- .env
+-- requirements.txt
```

## Requirements

- Python 3.10 or newer
- Node.js 18 or newer
- npm

## Environment Variables

Create a `.env` file in the project root:

```env
FIRECRAWL_API_KEY=
GROQ_API_KEY=
APOLLO_API_KEY=
NEWSAPI_KEY=
USE_MOCK_DATA=false
MAX_VALIDATOR_RETRIES=3
REQUEST_TIMEOUT_SECONDS=25
```

Use `USE_MOCK_DATA=false` when you want the backend to attempt live provider calls.

## Run The Backend

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8000
```

Health check:

```text
http://localhost:8000/api/health
```

## Run The Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

The frontend proxies `/api` and `/ws` requests to the backend on `localhost:8000`.

## Run The Smoke Test

From the project root:

```powershell
python scripts\smoke_test.py
```

The smoke test runs the pipeline across multiple industries and checks that the main report sections are produced.

## API Endpoints

- `GET /api/health`
- `GET /api/graph`
- `GET /api/runs`
- `POST /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/metrics`
- `POST /api/tracking/reply`
- `GET /track/open/{run_id}/{contact_key}/pixel.png`
- `GET /ws`

## Contact Intelligence Policy

The system only shows contact fields when a verified source returns concrete data. In live mode, it first attempts enrichment and then falls back to public company-source discovery from the target website. If no verified source returns an email, phone number, or profile URL, the field remains blank and is marked as `not_found`.

Example:

```json
{
  "email": {
    "value": "",
    "status": "not_found",
    "confidence": 0,
    "source": "",
    "trust_state": "not_found"
  },
  "verification_notes": [
    "No verified source returned contact data for this stakeholder."
  ]
}
```

## Demo Notes

- Use mock mode when a stable buildathon demo is more important than live provider availability.
- Use live mode when API keys are configured and external calls are allowed.
- Contact data is never guessed or fabricated.
- Outreach drafts are generated from the available research context.
