
import os
import math
import logging
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from supabase import create_client, Client

# ------------------------------------------
# Configuration
# ------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fish_farm_api")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase credentials are missing from backend/.env"
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Fish Farm Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "null",  # allows file:// origin in local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------
# Manual reading model
# ------------------------------------------

class Reading(BaseModel):
    temperature: float = Field(ge=-5, le=60)
    ph: float = Field(ge=0, le=14)
    predicted_do: float = Field(ge=0, le=30)


# ------------------------------------------
# Read latest row from Supabase
# ------------------------------------------

def latest_db_reading():
    response = (
        supabase.table("sensor_readings")
        .select(
            "id, thingspeak_entry_id, recorded_at, "
            "temperature, ph, predicted_do"
        )
        .order("recorded_at", desc=True)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


# ------------------------------------------
# Fetch latest ThingSpeak reading
# ------------------------------------------

def fetch_thingspeak_reading():
    channel_id = os.getenv("THINGSPEAK_CHANNEL_ID", "").strip()
    read_api_key = os.getenv(
        "THINGSPEAK_READ_API_KEY", ""
    ).strip()

    if not channel_id:
        raise HTTPException(
            status_code=500,
            detail="THINGSPEAK_CHANNEL_ID is missing from backend/.env",
        )

    url = (
        f"https://api.thingspeak.com/channels/"
        f"{channel_id}/feeds/last.json"
    )

    params = {}
    if read_api_key:
        params["api_key"] = read_api_key

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        feed = response.json()

    except requests.RequestException as exc:
        logger.exception("ThingSpeak request failed")
        raise HTTPException(
            status_code=502,
            detail="Could not retrieve readings from ThingSpeak.",
        ) from exc

    if not isinstance(feed, dict) or not feed.get("created_at"):
        raise HTTPException(
            status_code=404,
            detail="No ThingSpeak reading is available.",
        )

    try:
        entry_id = int(feed["entry_id"])
        temperature = float(feed["field1"])
        ph = float(feed["field2"])
        predicted_do = float(feed["field3"])

        values = [temperature, ph, predicted_do]

        if not all(math.isfinite(value) for value in values):
            raise ValueError("A sensor value is not finite.")

        if not -5 <= temperature <= 60:
            raise ValueError("Temperature is outside the accepted range.")

        if not 0 <= ph <= 14:
            raise ValueError("pH is outside the accepted range.")

        if not 0 <= predicted_do <= 30:
            raise ValueError("Predicted DO is outside the accepted range.")

    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid ThingSpeak reading: {exc}",
        ) from exc

    return {
        "thingspeak_entry_id": entry_id,
        "recorded_at": feed["created_at"],
        "temperature": temperature,
        "ph": ph,
        "predicted_do": predicted_do,
    }


# ------------------------------------------
# Home and status
# ------------------------------------------

@app.get("/")
def home():
    return {"message": "Fish Farm Monitoring API is running"}


@app.get("/api/status")
def api_status():
    return {
        "status": "online",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ------------------------------------------
# Test Supabase table access
# ------------------------------------------

@app.get("/api/supabase/check")
def check_supabase():
    try:
        response = (
            supabase.table("sensor_readings")
            .select("id")
            .limit(1)
            .execute()
        )

        return {
            "success": True,
            "message": "Supabase table is accessible.",
            "rows_found": len(response.data or []),
        }

    except Exception as exc:
        logger.exception("Supabase connection/table check failed")
        raise HTTPException(
            status_code=500,
            detail=f"Supabase check failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# ThingSpeak: fetch only
# ------------------------------------------

@app.get("/api/thingspeak/latest")
def get_thingspeak_latest():
    return fetch_thingspeak_reading()


# ------------------------------------------
# ThingSpeak -> Supabase sync
# ------------------------------------------

@app.get("/api/thingspeak/sync")
def sync_thingspeak_to_supabase():
    reading = fetch_thingspeak_reading()

    try:
        response = (
            supabase.table("sensor_readings")
            .upsert(
                reading,
                on_conflict="thingspeak_entry_id",
            )
            .execute()
        )

        logger.info(
            "ThingSpeak entry %s synced successfully",
            reading["thingspeak_entry_id"],
        )

        return {
            "success": True,
            "message": "ThingSpeak reading synced to Supabase.",
            "data": response.data,
        }

    except Exception as exc:
        # This prints the real error in the VS Code terminal.
        logger.exception("SUPABASE SYNC FAILED")

        # This exposes the error detail in the local API response.
        raise HTTPException(
            status_code=500,
            detail=f"Supabase sync failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# Sensor cards: values from Supabase
# ------------------------------------------

@app.get("/api/sensors")
def get_sensors():
    try:
        reading = latest_db_reading()

        if not reading:
            return {
                "temperature": None,
                "temperature_status": "WAITING",
                "ph": None,
                "ph_status": "WAITING",
            }

        temperature = reading["temperature"]
        ph = reading["ph"]

        return {
            "temperature": temperature,
            "temperature_status": (
                "SAFE" if 25 <= temperature <= 32 else "NOT SAFE"
            ),
            "ph": ph,
            "ph_status": (
                "SAFE" if 6.5 <= ph <= 8.5 else "NOT SAFE"
            ),
        }

    except Exception as exc:
        logger.exception("Could not retrieve sensor readings")
        raise HTTPException(
            status_code=500,
            detail=f"Sensor retrieval failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# Manual reading insertion
# ------------------------------------------

@app.post("/api/readings")
def save_reading(reading: Reading):
    record = {
        "temperature": reading.temperature,
        "ph": reading.ph,
        "predicted_do": reading.predicted_do,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        response = (
            supabase.table("sensor_readings")
            .insert(record)
            .execute()
        )

        return {
            "message": "Reading saved successfully",
            "data": response.data,
        }

    except Exception as exc:
        logger.exception("Manual Supabase insert failed")
        raise HTTPException(
            status_code=500,
            detail=f"Manual save failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# Latest saved reading
# ------------------------------------------

@app.get("/api/readings/latest")
def get_latest_reading():
    try:
        return {"data": latest_db_reading()}

    except Exception as exc:
        logger.exception("Latest reading query failed")
        raise HTTPException(
            status_code=500,
            detail=f"Latest reading query failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# Historical readings for graphs
# ------------------------------------------

@app.get("/api/readings/history")
def get_reading_history():
    try:
        response = (
            supabase.table("sensor_readings")
            .select(
                "id, recorded_at, temperature, ph, predicted_do"
            )
            .order("recorded_at", desc=True)
            .limit(12)
            .execute()
        )

        return {"data": list(reversed(response.data or []))}

    except Exception as exc:
        logger.exception("Reading history query failed")
        raise HTTPException(
            status_code=500,
            detail=f"History query failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# Predicted dissolved oxygen
# ------------------------------------------

@app.get("/api/prediction")
def get_prediction():
    try:
        reading = latest_db_reading()

        if not reading:
            return {
                "predicted_do": None,
                "unit": "mg/L",
                "source": "Waiting for ThingSpeak sync",
            }

        return {
            "predicted_do": reading["predicted_do"],
            "unit": "mg/L",
            "source": "ESP32 ML model via ThingSpeak",
            "recorded_at": reading["recorded_at"],
        }

    except Exception as exc:
        logger.exception("Prediction query failed")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction query failed: {str(exc)}",
        ) from exc


# ------------------------------------------
# Basic water-quality insights
# ------------------------------------------

@app.get("/api/insights")
def get_insights():
    try:
        reading = latest_db_reading()

        if not reading:
            return {
                "insights": [
                    "Waiting for the first synchronized reading."
                ]
            }

        temperature = reading["temperature"]
        ph = reading["ph"]
        predicted_do = reading["predicted_do"]

        insights = [
            (
                "Temperature is within the configured example range."
                if 25 <= temperature <= 32
                else "Temperature is outside the configured example range."
            ),
            (
                "pH is within the configured example range."
                if 6.5 <= ph <= 8.5
                else "pH is outside the configured example range."
            ),
            f"ESP32 predicted dissolved oxygen: {predicted_do:.2f} mg/L.",
        ]

        return {"insights": insights}

    except Exception as exc:
        logger.exception("Insight generation failed")
        raise HTTPException(
            status_code=500,
            detail=f"Insight generation failed: {str(exc)}",
        ) from exc
