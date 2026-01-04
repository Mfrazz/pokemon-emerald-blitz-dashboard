import os
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# ---------- CONFIG ----------
CSV_DIR = r"C:\Users\Matt\Documents\Pokemon With Friends\Python Projects\downloads\downloads_with_timestamp"  # folder with timestamped files
DB_PATH = "sqlite:///PokemonDraftData.db"     # your database
TABLE_NAME = "all_draft_csv_with_website"

engine = create_engine(DB_PATH)

for filename in os.listdir(CSV_DIR):
    if not filename.lower().endswith(".csv"):
        continue

    file_path = os.path.join(CSV_DIR, filename)

    try:
        ts_str = filename[:15]  # first 15 characters YYYYMMDD_HHMMSS
        date_val = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
    except Exception as e:
        print(f"Failed to parse timestamp from {filename}: {e}")
        continue

    # --- Read CSV ---
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Failed to read {filename}: {e}")
        continue

    if 'Player' in df.columns:
        df = df.rename(columns={'Player': 'Pokemon'})

        # --- Add Date column ---
    df['date'] = date_val

    # Normalize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # --- Insert into database ---
    try:
        df.to_sql(
            TABLE_NAME,
            engine,
            if_exists='append',  # append to existing table
            index=False
        )
        print(f"Inserted {filename} into {TABLE_NAME}")
    except Exception as e:
        print(f"Failed to insert {filename}: {e}")