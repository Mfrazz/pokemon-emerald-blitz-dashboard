import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
import os

# --------------------
# Configuration
# --------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "PokemonDraftData.db")

# Connect to SQLite database
conn = sqlite3.connect(DB_PATH)

st.title("Pokémon Emerald Blitz Draft Data")

# ----------------------------
# TOP CHART — PATCH FILTERED
# ----------------------------
st.header("Top / Bottom Pokémon by Patch")

# --- UI CONTROLS ---
patches_df = pd.read_sql("""
    SELECT DISTINCT patch
    FROM draft_event_v2
    WHERE patch IS NOT NULL
    ORDER BY patch DESC
""", conn)

patch_list = patches_df["patch"].tolist()

selected_patch = st.selectbox(
    "Select Patch",
    patch_list
)

top_bottom = st.radio(
    "Show",
    ["Top", "Bottom"],
    horizontal=True
)

x_limit = st.slider(
    "Number of Pokémon",
    min_value=5,
    max_value=30,
    value=10,
    step=1
)

order_direction = "DESC" if top_bottom == "Top" else "ASC"

# ----------------------------
# DATA QUERY
# ----------------------------
query = f"""
SELECT
    p.pokemon,
    ROUND(AVG(p.cost), 2) AS avg_cost,
    COUNT(*) AS times_drafted
FROM draft_pokemon_v2 p
JOIN draft_event_v2 d
    ON p.draft_id = d.id
WHERE d.patch = ?
GROUP BY p.pokemon
ORDER BY avg_cost {order_direction}
LIMIT {x_limit}
"""

df = pd.read_sql(query, conn, params=(selected_patch,))

# ----------------------------
# CHART
# ----------------------------
if df.empty:
    st.warning("No data available for this patch.")
else:
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X(
                "avg_cost:Q",
                title="Average Cost",
                scale=alt.Scale(zero=False)
            ),
            y=alt.Y(
                "pokemon_name:N",
                sort="-x",
                title="Pokémon"
            ),
            tooltip=[
                alt.Tooltip("pokemon_name:N", title="Pokémon"),
                alt.Tooltip("avg_cost:Q", title="Avg Cost"),
                alt.Tooltip("times_drafted:Q", title="Times Drafted")
            ]
        )
        .properties(
            width=700,
            height=400,
            title=f"{top_bottom} {x_limit} Pokémon — Patch {selected_patch}"
        )
    )

    st.altair_chart(chart, use_container_width=True)

# --------------------
# Draft Pick Order Visualization
# --------------------

st.header("Pokémon Costs by Draft (Draft Order)")

# -----------------------------
# Load all draft IDs
# -----------------------------
draft_ids_df = pd.read_sql_query("""
    SELECT DISTINCT draft_id
    FROM draft_pokemon_v2
    ORDER BY draft_id
""", conn)

draft_ids = draft_ids_df["draft_id"].tolist()

# Draft selector
selected_draft = st.selectbox(
    "Select Draft",
    draft_ids
)

# -----------------------------
# Load data for selected draft
# -----------------------------
df = pd.read_sql_query("""
    SELECT
        draft_id,
        draft_order,
        pokemon,
        drafted_by,
        cost
    FROM draft_pokemon_v2
    WHERE draft_id = ?
    ORDER BY draft_order
""", conn, params=(selected_draft,))

# Safety check
if df.empty:
    st.warning("No data found for this draft.")
    st.stop()

# -----------------------------
# Average cost
# -----------------------------
avg_cost = df["cost"].mean()

# -----------------------------
# Bar chart (colored by drafter)
# -----------------------------
bars = alt.Chart(df).mark_bar().encode(
    x=alt.X(
        "draft_order:O",
        title="Draft Order"
    ),
    y=alt.Y(
        "cost:Q",
        title="Cost"
    ),
    color=alt.Color(
        "drafted_by:N",
        title="Drafted By",
        legend=alt.Legend(orient="right")
    ),
    tooltip=[
        alt.Tooltip("draft_order:Q", title="Pick"),
        alt.Tooltip("pokemon:N", title="Pokémon"),
        alt.Tooltip("drafted_by:N", title="Drafted By"),
        alt.Tooltip("cost:Q", title="Cost")
    ]
)

# -----------------------------
# Average cost line
# -----------------------------
avg_line = alt.Chart(
    pd.DataFrame({"avg_cost": [avg_cost]})
).mark_rule(
    color="red",
    strokeDash=[6, 4],
    size=2
).encode(
    y="avg_cost:Q"
)

# -----------------------------
# Combine & render
# -----------------------------
chart = (bars + avg_line).properties(
    width=1000,
    height=450,
    title=f"Draft {selected_draft} – Pokémon Cost by Draft Order (Avg: {round(avg_cost, 1)})"
)

st.altair_chart(chart, use_container_width=True)


# Load top 3 Pokémon per draft
df_top3 = pd.read_sql_query("SELECT * FROM vw_top3_pokemon_per_draft;", conn)


st.header("Top 3 Most Expensive Pokémon per Draft")
st.write("This chart shows the top 3 most expensive Pokémon for each draft.")

top3_chart = alt.Chart(df_top3).mark_bar().encode(
    x='pokemon:N',               # Pokémon names on x-axis
    y='cost:Q',                  # Cost on y-axis
    color='draft_id:N',          # Different color for each draft
    tooltip=['draft_id', 'pokemon', 'drafted_by', 'cost', 'draft_order']  # hover info
).properties(width=700)

st.altair_chart(top3_chart)



