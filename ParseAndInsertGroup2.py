import csv
import os
from datetime import datetime
from sqlalchemy import create_engine, text

DB_PATH = "sqlite:///PokemonDraftData.db"
CSV_DIR = r"C:\Users\Matt\Documents\Pokemon With Friends\Python Projects\downloads\CSVs With Format"

engine = create_engine(DB_PATH)

def process_group2_csv(file_path):
    with open(file_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    # ---- HEADER PARSING ----
    total_sold = int(rows[1][0].split(":")[1])

    # date from filename (YYYYMMDD_HHMMSS_...)
    date_part = rows[0][0].replace("Date:", "").strip()
    time_part = rows[0][1].strip()

    raw_datetime = f"{date_part}, {time_part}"

    date_time = datetime.strptime(
        raw_datetime,
        "%m/%d/%Y, %I:%M:%S %p"
    )

    # ---- FIND TABLE SPLITS ----
    helper_start = None
    draft_start = None

    for i, row in enumerate(rows):
        if row[:3] == ["Player", "Starting Money", "Remaining Money"]:
            helper_start = i + 1
        if row[:3] == ["Pokemon", "Drafted By", "Cost"]:
            draft_start = i + 1
            helper_end = i - 1
            break

    helper_rows = rows[helper_start:helper_end]
    draft_rows = rows[draft_start:]

    with engine.begin() as conn:
        # ---- INSERT DRAFT EVENT ----
        result = conn.execute(
            text("""
            INSERT INTO draft_event (date_time, total_pokemon_sold)
            VALUES (:dt, :total)
            """),
            {"dt": date_time, "total": total_sold}
        )
        draft_id = result.lastrowid

        # ---- INSERT PLAYERS ----
        for r in helper_rows:
            if not r or not r[0]:
                continue
            conn.execute(
                text("""
                INSERT INTO draft_players
                (draft_id, player_name, starting_money, remaining_money)
                VALUES (:did, :p, :s, :r)
                """),
                {
                    "did": draft_id,
                    "p": r[0],
                    "s": int(r[1]),
                    "r": int(r[2])
                }
            )

        # ---- INSERT POKEMON ----
        for r in draft_rows:
            if not r or not r[0]:
                continue
            conn.execute(
                text("""
                INSERT INTO draft_pokemon
                (draft_id, pokemon, drafted_by, cost)
                VALUES (:did, :poke, :by, :cost)
                """),
                {
                    "did": draft_id,
                    "poke": r[0],
                    "by": r[1],
                    "cost": int(r[2])
                }
            )

    print(f"Inserted {os.path.basename(file_path)}")

# ---- RUN ALL FILES ----
for file in os.listdir(CSV_DIR):
    if file.lower().endswith(".csv"):
        process_group2_csv(os.path.join(CSV_DIR, file))