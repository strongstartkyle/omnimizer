"""
process_client.py — Local Coach Tool
=====================================
Run this on your PC whenever a client sends you their Apple Health export.
It processes the XML locally (no timeouts) and pushes the result to Supabase
so it appears immediately in their dashboard.

Usage:
    python process_client.py

You will be prompted to select a client and provide the XML file path.

Requirements:
    pip install pandas supabase
"""

import os
import sys
import pandas as pd
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG — loaded from .env
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# =========================
# SETUP
# =========================
sys.path.insert(0, os.path.dirname(__file__))
from insight_engine import run_engine

sb = create_client(SUPABASE_URL, SUPABASE_KEY)


def list_clients():
    res = sb.table("clients").select("id, name, targets").eq("active", True).execute()
    return res.data or []


def push_to_supabase(client_id: str, df: pd.DataFrame):
    csv_str = df.to_csv(index=False)
    sb.table("dashboard_cache").upsert({
        "client_id": client_id,
        "csv_data": csv_str,
        "updated_at": datetime.utcnow().isoformat()
    }).execute()


def main():
    print("\nOmnimizer - Local Client Data Processor")
    print("=" * 45)

    # List clients
    clients = list_clients()
    if not clients:
        print("No active clients found. Add clients via the coach dashboard first.")
        return

    print("\nActive clients:")
    for i, c in enumerate(clients):
        print(f"  [{i + 1}] {c['name']}")

    # Select client
    while True:
        try:
            choice = int(input("\nSelect client number: ")) - 1
            if 0 <= choice < len(clients):
                client = clients[choice]
                break
            else:
                print(f"Please enter a number between 1 and {len(clients)}")
        except ValueError:
            print("Please enter a valid number")

    print(f"\nSelected: {client['name']}")

    # Get XML path
    while True:
        xml_path = input("\nDrag and drop export.xml here (or type the full path): ").strip().strip('"').strip("'")
        if os.path.exists(xml_path):
            break
        else:
            print(f"File not found: {xml_path}. Please check the path and try again.")

    # Process
    print(f"\nProcessing {client['name']}'s data...")
    print(f"   File size: {os.path.getsize(xml_path) / 1024 / 1024:.1f} MB")

    targets = client.get("targets") or {
        "calories": 2500,
        "steps": 8000,
        "water": 2500,
        "sleep": 7.5,
        "weight_change_pct_per_week": -0.75
    }

    with open(xml_path, "rb") as f:
        xml_bytes = f.read()

    df = run_engine(xml_bytes, targets)

    if df is None or df.empty:
        print("ERROR: No matching health data found in the file. Check the export is valid.")
        return

    print(f"   Parsed {len(df)} days of data")
    print(f"   Range: {df['date'].min().strftime('%d %b %Y')} -> {df['date'].max().strftime('%d %b %Y')}")

    # Push to Supabase
    print(f"\nPushing to Supabase...")
    push_to_supabase(client["id"], df)
    print(f"   Done! {client['name']}'s dashboard has been updated.")
    print(f"\n   View at: your-app-url.streamlit.app\n")


if __name__ == "__main__":
    main()
