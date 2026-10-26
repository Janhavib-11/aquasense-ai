# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] — 2026-10-26

### Added
- FastAPI backend with 10 REST endpoints
- Supabase integration (`sensor_readings` table, upsert on ThingSpeak entry ID)
- ThingSpeak polling and sync endpoint
- ESP32 ML-predicted dissolved oxygen field support
- Single-page frontend (no build step) wired to all endpoints
- Live sensor cards with SAFE/NOT SAFE classification
- SVG sparklines and history charts built from `/api/readings/history`
- Manual reading form (`POST /api/readings`)
- Alert system derived from live sensor status
- ThingSpeak raw feed viewer
- Supabase health check endpoint
- Dark and light theme with system preference detection
- Auto-refresh polling every 60 seconds
- CORS configured for localhost:5173 and file:// origin

### Backend
- Pydantic v2 validation on all inputs
- Structured logging via Python `logging`
- Graceful error handling with HTTP status codes and detail messages
- `test_supabase.py` for pre-flight connectivity check
