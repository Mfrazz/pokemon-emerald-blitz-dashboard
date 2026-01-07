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

#NEW CHART AVERAGE COST FOR EACH POKEMON

df_avg_pokemon = pd.read_sql_query("""
    SELECT pokemon, ROUND(AVG(cost), 2) AS avg_cost, COUNT(*) AS times_drafted
    FROM draft_pokemon_v2
    GROUP BY pokemon
""", conn)

# --------------------
# Streamlit UI
# --------------------
st.header("Average Cost per Pokémon Across All Drafts")
st.write("Shows the average draft price of each Pokémon and how often it was drafted.")

# Top/Bottom selector
filter_type = st.radio("Show Top or Bottom Pokémon by Average Cost", ("Top", "Bottom"))
x = st.number_input("How many Pokémon to show?", min_value=1, max_value=len(df_avg_pokemon), value=10)

# Sort data based on Top or Bottom
df_avg_pokemon_sorted = df_avg_pokemon.sort_values(
    by='avg_cost',
    ascending=(filter_type == "Bottom")  # Bottom = ascending, Top = descending
)

# Take top/bottom X Pokémon
df_avg_pokemon_filtered = df_avg_pokemon_sorted.head(x)

# --------------------
# Altair color scale (light blue → dark blue)
# --------------------
color_scale = alt.Scale(
    domain=[df_avg_pokemon_filtered['times_drafted'].min(),
            df_avg_pokemon_filtered['times_drafted'].max()],
    range=['#9999FF', '#000099']  # light blue → dark blue
)

# --------------------
# Create bar chart
# --------------------
avg_pokemon_chart = alt.Chart(df_avg_pokemon_filtered).mark_bar().encode(
    x=alt.X('pokemon:N', sort=df_avg_pokemon_filtered['pokemon'].tolist()),
    y='avg_cost:Q',
    color=alt.Color('times_drafted:Q', scale=color_scale, legend=alt.Legend(title="Times Drafted")),
    tooltip=['pokemon', 'avg_cost', 'times_drafted']
).properties(width=1000)

st.altair_chart(avg_pokemon_chart)

# NEW CHART: AVERAGE COST PER POKEMON BY PATCH

# Get list of patches from draft_event_v2
patches = pd.read_sql_query("""
    SELECT DISTINCT patch
    FROM draft_event_v2
    ORDER BY patch
""", conn)['patch'].tolist()

# Streamlit UI
st.header("Average Cost per Pokémon by Patch")
st.write("Shows the average draft price of each Pokémon and how often it was drafted, filtered by patch.")

# Patch selector
selected_patch = st.selectbox("Select Patch", patches)

# Pull Pokémon data for the selected patch
df_avg_pokemon_patch = pd.read_sql_query(f"""
    SELECT dp.pokemon,
           ROUND(AVG(dp.cost), 2) AS avg_cost,
           COUNT(*) AS times_drafted
    FROM draft_pokemon_v2 dp
    JOIN draft_event_v2 de ON dp.draft_id = de.id
    WHERE de.patch = '{selected_patch}'
    GROUP BY dp.pokemon
""", conn)

# Top/Bottom selector
filter_type_patch = st.radio(f"Show Top or Bottom Pokémon by Average Cost ({selected_patch})", ("Top", "Bottom"))
x_patch = st.number_input(f"How many Pokémon to show for {selected_patch}?",
                          min_value=1, max_value=len(df_avg_pokemon_patch), value=10, key="patch_num")

# Sort data based on Top or Bottom
df_avg_pokemon_patch_sorted = df_avg_pokemon_patch.sort_values(
    by='avg_cost',
    ascending=(filter_type_patch == "Bottom")  # Bottom = ascending, Top = descending
)

# Take top/bottom X Pokémon
df_avg_pokemon_patch_filtered = df_avg_pokemon_patch_sorted.head(x_patch)

# Altair color scale (light blue → dark blue)
color_scale_patch = alt.Scale(
    domain=[df_avg_pokemon_patch_filtered['times_drafted'].min(),
            df_avg_pokemon_patch_filtered['times_drafted'].max()],
    range=['#9999FF', '#000099']  # light blue → dark blue
)

# Create bar chart
avg_pokemon_patch_chart = alt.Chart(df_avg_pokemon_patch_filtered).mark_bar().encode(
    x=alt.X('pokemon:N', sort=df_avg_pokemon_patch_filtered['pokemon'].tolist()),
    y='avg_cost:Q',
    color=alt.Color('times_drafted:Q', scale=color_scale_patch, legend=alt.Legend(title="Times Drafted")),
    tooltip=['pokemon', 'avg_cost', 'times_drafted']
).properties(width=1000)

st.altair_chart(avg_pokemon_patch_chart)

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



