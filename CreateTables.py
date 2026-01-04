from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///PokemonDraftData.db")

with engine.begin() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS draft_event_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        external_draft_id TEXT,
        date_time DATETIME,
        total_pokemon_sold INTEGER
    );
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS draft_players_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draft_id INTEGER,
        player_name TEXT,
        starting_money INTEGER,
        remaining_money INTEGER,
        FOREIGN KEY (draft_id) REFERENCES draft_event_v2(id)
    );
    """))

    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS draft_pokemon_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draft_id INTEGER,
        draft_order INTEGER,
        pokemon TEXT,
        drafted_by TEXT,
        cost INTEGER,
        FOREIGN KEY (draft_id) REFERENCES draft_event_v2(id)
    );
    """))

print("V2 tables ready.")

