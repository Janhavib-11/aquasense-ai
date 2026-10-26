# AquaSense AI

> Real-time water quality monitoring and predictive analytics for fish farms.

An ESP32 microcontroller runs an onboard ML model that predicts dissolved oxygen (DO) and pushes temperature, pH, and predicted DO to ThingSpeak. This FastAPI backend syncs those readings into Supabase and exposes a clean REST API consumed by the single-page frontend.

---

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Contributing](#contributing)
- [License](#license)

---

## Architecture

```
ESP32  (ML model onboard)
  │   field1=temperature  field2=pH  field3=predicted_DO
  ▼
ThingSpeak  (IoT cloud)
  │   GET /channels/{id}/feeds/last.json
  ▼
FastAPI backend  ──────────────►  Supabase  (PostgreSQL)
  │   uvicorn  port 8000              sensor_readings table
  │
  └──────────────────────────────►  frontend/index.html
                                      served on port 5173
```

---

## Project Structure

```
aquasense/
├── backend/
│   ├── main.py              # All FastAPI routes and business logic
│   ├── test_supabase.py     # Standalone Supabase connectivity test
│   ├── requirements.txt     # Pinned Python dependencies
│   ├── .env.example         # Environment variable template
│   └── .gitignore
├── frontend/
│   └── index.html           # Single-page app — all 10 endpoints wired
├── README.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

---

## Prerequisites

| Tool | Version |
|---|---|
| Python | ≥ 3.10 |
| pip | latest |
| Supabase project | with `sensor_readings` table |
| ThingSpeak channel | with field1, field2, field3 |
| ESP32 firmware | publishing to the above channel |

---

## Backend Setup

### 1. Clone and enter the backend directory

```bash
git clone https://github.com/YOUR_USERNAME/aquasense-ai.git
cd aquasense-ai/backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
```

Edit `.env` with your credentials (see [Environment Variables](#environment-variables)).

### 5. Verify Supabase connection

```bash
python test_supabase.py
```

Expected output:
```
Supabase connection successful!
Table is accessible.
Rows returned: N
```

### 6. Start the API server

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs: http://127.0.0.1:8000/docs

---

## Frontend Setup

No build step is required. The frontend is a single HTML file.

### Serve with Python (recommended — avoids CORS issues)

```bash
python -m http.server 5173 --directory frontend
```

Open **http://localhost:5173** in your browser.

### Direct file open (development only)

Open `frontend/index.html` directly. The backend allows `null` origin for local development.

---

## API Reference

All endpoints are served at `http://127.0.0.1:8000`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Root health check |
| GET | `/api/status` | API online status and timestamp |
| GET | `/api/sensors` | Latest temperature and pH with SAFE/NOT SAFE status |
| GET | `/api/prediction` | Latest predicted dissolved oxygen from ESP32 ML model |
| GET | `/api/readings/latest` | Full latest row from Supabase |
| GET | `/api/readings/history` | Last 12 readings for chart display |
| GET | `/api/insights` | Text-based water quality insights |
| GET | `/api/thingspeak/latest` | Raw latest feed from ThingSpeak (not stored) |
| GET | `/api/thingspeak/sync` | Sync ThingSpeak → Supabase (upsert on entry ID) |
| GET | `/api/supabase/check` | Supabase table connectivity check |
| POST | `/api/readings` | Manually insert a reading into Supabase |

### POST /api/readings — Request body

```json
{
  "temperature": 28.5,
  "ph": 7.2,
  "predicted_do": 7.8
}
```

---

## Environment Variables

Copy `.env.example` to `.env` and populate:

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon or service role key |
| `THINGSPEAK_CHANNEL_ID` | ✅ | ThingSpeak channel ID |
| `THINGSPEAK_READ_API_KEY` | Optional | Required for private channels |

### Supabase `sensor_readings` table schema

```sql
create table sensor_readings (
  id                  bigserial primary key,
  thingspeak_entry_id bigint unique,
  recorded_at         timestamptz not null default now(),
  temperature         real not null,
  ph                  real not null,
  predicted_do        real not null
);
```

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## License

MIT — see [LICENSE](./LICENSE).
