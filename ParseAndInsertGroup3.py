import csv
import os
from datetime import datetime
from sqlalchemy import create_engine, text

# ---------------- CONFIG ----------------
CSV_DIR = r"C:\Users\Matt\Documents\Pokemon With Friends\Python Projects\downloads"          # your bot output folder
DB_PATH = "sqlite:///PokemonDraftData.db"
# ----------------------------------------

engine = create_engine(DB_PATH)


# ---------- DATETIME PARSER ----------
def parse_datetime(raw: str) -> datetime:
    raw = raw.strip()

    formats = [
        "%d/%m/%Y %H:%M:%S",      # 31/12/2025 18:02:28
        "%m/%d/%Y %I:%M:%S %p",   # 12/31/2025 6:02:28 PM
        "%m/%d/%Y %H:%M:%S",      # fallback
    ]

    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue

    raise ValueError(f"Unrecognized datetime format: {raw}")


# ---------- DUPLICATE CHECK ----------
def draft_exists(external_draft_id: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT 1
                FROM draft_event_v2
                WHERE external_draft_id = :eid
                LIMIT 1
            """),
            {"eid": external_draft_id}
        ).fetchone()

    return result is not None


# ---------- MAIN PARSER ----------
def process_group3_csv(file_path):
    with open(file_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    external_draft_id = None
    date_time = None
    total_sold = None
    patch = None

    # ---------- HEADER SCAN ----------
    for row in rows:
        if not row:
            continue

        if row[0].startswith("Draft ID:"):
            external_draft_id = row[0].split(":", 1)[1].strip()

        if row[0].startswith("Patch:"):
            patch = row[0].split(":", 1)[1].strip()

        elif row[0].startswith("Date:"):
            date_part = row[0].replace("Date:", "").strip()
            time_part = row[1].strip() if len(row) > 1 else ""
            raw_datetime = f"{date_part} {time_part}".strip()
            date_time = parse_datetime(raw_datetime)

        elif row[0].startswith("Total Pokemon Sold:"):
            total_sold = int(row[0].split(":", 1)[1])

    # ---------- Skip Bad Draft IDs ------
    if external_draft_id in ('860538035132', '072501118051'):
        print(f"Skipping bad draft ID: {external_draft_id}")
        return

    # ---------- DUPLICATE SKIP ----------
    if draft_exists(external_draft_id):
        print(f"Skipping already ingested draft {external_draft_id}")
        return

    if not all([external_draft_id, patch, date_time, total_sold]):
        raise ValueError(f"Missing header data in {os.path.basename(file_path)}")

    # ---------- FIND TABLES ----------
    players_start = None
    order_start = None

    for i, row in enumerate(rows):
        if row[:3] == ["Player", "Starting Money", "Remaining Money"]:
            players_start = i + 1

        elif row[:4] == ["Order", "Pokemon", "Drafted By", "Cost"]:
            players_end = i - 1
            order_start = i + 1
            break

    players_rows = rows[players_start:players_end]
    order_rows = rows[order_start:]

    # ---------- DATABASE INSERT ----------
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                INSERT INTO draft_event_v2
                (external_draft_id, patch, date_time, total_pokemon_sold)
                VALUES (:eid,:patch, :dt, :total)
            """),
            {
                "eid": external_draft_id,
                "patch": patch,
                "dt": date_time,
                "total": total_sold
            }
        )
        draft_event_id = result.lastrowid

        for r in players_rows:
            if not r or not r[0]:
                continue

            conn.execute(
                text("""
                    INSERT INTO draft_players_v2
                    (draft_id, player_name, starting_money, remaining_money)
                    VALUES (:d, :p, :s, :r)
                """),
                {
                    "d": draft_event_id,
                    "p": r[0],
                    "s": int(r[1]),
                    "r": int(r[2])
                }
            )

        for r in order_rows:
            if not r or not r[0]:
                continue

            conn.execute(
                text("""
                    INSERT INTO draft_pokemon_v2
                    (draft_id, draft_order, pokemon, drafted_by, cost)
                    VALUES (:d, :o, :p, :by, :c)
                """),
                {
                    "d": draft_event_id,
                    "o": int(r[0]),
                    "p": r[1],
                    "by": r[2],
                    "c": int(r[3])
                }
            )

    print(f"Inserted draft {external_draft_id}")

for file in os.listdir(CSV_DIR):
    if file.lower().endswith(".csv"):
        process_group3_csv(os.path.join(CSV_DIR, file))


