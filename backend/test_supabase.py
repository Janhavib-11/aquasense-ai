
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise ValueError(
        "Supabase credentials missing. Check your backend/.env file."
    )

supabase = create_client(url, key)

result = (
    supabase.table("sensor_readings")
    .select("id")
    .limit(1)
    .execute()
)

print("Supabase connection successful!")
print("Table is accessible.")
print("Rows returned:", len(result.data))
