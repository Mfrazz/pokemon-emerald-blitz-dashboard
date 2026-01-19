import sqlite3

DB_PATH = "PokemonDraftData.db"

OLD_NAME = "mega falinks"
NEW_NAME = "Falinks"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Preview how many rows will be affected
cursor.execute(
    """
    SELECT COUNT(*)
    FROM draft_pokemon_v2
    WHERE LOWER(pokemon) = ?
    """,
    (OLD_NAME,)
)

count = cursor.fetchone()[0]
print(f"Found {count} rows with pokemon = '{OLD_NAME}'")

if count > 0:
    cursor.execute(
        """
        UPDATE draft_pokemon_v2
        SET pokemon = ?
        WHERE LOWER(pokemon) = ?
        """,
        (NEW_NAME, OLD_NAME)
    )

    conn.commit()
    print("Update complete ✅")
else:
    print("No rows to update.")

conn.close()