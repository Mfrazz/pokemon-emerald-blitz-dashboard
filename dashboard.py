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

# --------------------
# Draft Pick Order Visualization (Fixed)
# --------------------

st.header("Draft Pick Order – Full Draft View")

# Load draft pick data
df_draft_picks = pd.read_sql_query("""
    SELECT
        draft_id,
        "order" AS draft_order,
        pokemon,
        drafted_by,
        cost
    FROM draft_pokemon_v2
    ORDER BY draft_id, draft_order
""", conn)

# Draft selector
draft_ids = sorted(df_draft_picks["draft_id"].unique())

selected_draft = st.selectbox(
    "Select a Draft",
    draft_ids
)

df_selected_draft = df_draft_picks[
    df_draft_picks["draft_id"] == selected_draft
]

# Calculate average cost for the selected draft
avg_cost = df_selected_draft["cost"].mean()

# Dynamically scale width based on number of picks
chart_width = max(900, len(df_selected_draft) * 30)

# Bar chart (each Pokémon is a single bar)
bars = alt.Chart(df_selected_draft).mark_bar().encode(
    x=alt.X(
        "draft_order:O",
        title="Draft Order",
        sort=list(df_selected_draft["draft_order"])
    ),
    y=alt.Y("cost:Q", title="Cost"),
    color=alt.Color(
        "drafted_by:N",
        title="Drafted By",
        legend=alt.Legend(orient="right")
    ),
    tooltip=[
        alt.Tooltip("draft_order:O", title="Pick"),
        alt.Tooltip("pokemon:N", title="Pokémon"),
        alt.Tooltip("drafted_by:N", title="Drafted By"),
        alt.Tooltip("cost:Q", title="Cost")
    ]
)

# Average cost line
avg_line = alt.Chart(
    pd.DataFrame({"avg_cost": [avg_cost]})
).mark_rule(
    color="red",
    strokeDash=[6, 4]
).encode(
    y="avg_cost:Q"
)

# Combine chart
draft_order_chart = (bars + avg_line).properties(
    width=chart_width,
    height=450,
    title=f"Draft {selected_draft} – Pokémon Draft Order (Avg Cost: {round(avg_cost, 1)})"
)

st.altair_chart(draft_order_chart, use_container_width=True)

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

draft_filter = st.selectbox("Select Draft", options=df_top3['draft_id'].unique())
df_top3_filtered = df_top3[df_top3['draft_id'] == draft_filter]

filtered_chart = alt.Chart(df_top3_filtered).mark_bar().encode(
    x='pokemon:N',
    y='cost:Q',
    color='draft_id:N',
    tooltip=['draft_id', 'pokemon', 'drafted_by', 'cost', 'draft_order']
).properties(width=700)

st.altair_chart(filtered_chart)

