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

st.set_page_config(page_title="Pokemon Blitz Data Dashboard")

tab_welcome, tab_global, tab_patch, tab_players, tab_appendix = st.tabs([
    "Welcome",
    "All Draft Data",
    "Patch Trends",
    "Player Data",
    "Appendix"
])

#Add all information for Welcome tab here

with tab_welcome:
    st.title("Pokémon Emerald Blitz Dashboard")

    st.markdown("""
    Welcome to the **Pokémon Emerald Blitz Draft Dashboard**!

    This dashboard provides insights into:
    - Draft trends across all time
    - How patches affect the meta
    - Player behavior and preferences
    - Full access to the underlying data
    """)

    st.subheader("Links")
    st.markdown("""
    - 💬 [Discord](https://discord.gg/YOUR_LINK_HERE)
    - 📄 Rules & Format (link coming soon)
    - 📊 GitHub Repository (optional)
    """)

    st.info("Use the tabs above to explore the data.")

#tab for all data across all patches

with tab_global:
    st.header("All Draft Data (All Patches Combined)")

    st.markdown("""
    This section shows draft data **across all drafts**, regardless of patch.
    """)

    st.subheader("Average Cost per Pokémon Across All Drafts")

    # NEW CHART AVERAGE COST FOR EACH POKEMON

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

    st.subheader("Other Global Insights (Coming Soon)")
    st.write("- Most expensive Pokémon ever drafted")
    st.write("- Most frequently drafted Pokémon")
    st.write("- Players with the most drafts")

    #--------------------
    #Draft Pick Order Visualization
    #--------------------

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
                           SELECT draft_id,
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

#tab for patch specific data

with tab_patch:
    st.header("Patch-Based Draft Trends")

    st.markdown("""
    Analyze how draft behavior changes between patches.
    """)

    st.subheader("Top / Bottom Pokémon by Patch")
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

with tab_players:
    st.header("Player Data by Patch")

    st.markdown("""
    Explore player behavior and performance across patches.
    """)



    st.subheader("Player Draft Trends")

    # --------------------
    # Streamlit UI
    # --------------------
    st.header("Player Signature Pokémon (All Patches)")
    st.write(
        "Shows Pokémon that players consistently pick when available. "
        "Only includes players with 3+ drafts and Pokémon that were available 3+ times. "
        "Bars show the percent of drafts in which the player picked the Pokémon. "
        "Super signature picks (>80%) are highlighted in red."
    )


    # --------------------
    # SQL: calculate signature picks
    # --------------------
    SQL_QUERY = """
                WITH player_stats AS (
                    -- Count how many drafts each player drafted each pokemon at least once
                    SELECT LOWER(pp.drafted_by)        AS drafted_by, \
                           pp.pokemon, \
                           COUNT(DISTINCT pp.draft_id) AS times_drafted
                    FROM draft_pokemon_v2 pp
                    GROUP BY LOWER(pp.drafted_by), pp.pokemon),
                     pokemon_available AS (
                         -- Count how many drafts each player saw each pokemon at least once
                         SELECT LOWER(dp.player_name)       AS drafted_by, \
                                pp.pokemon, \
                                COUNT(DISTINCT dp.draft_id) AS times_available
                         FROM draft_players_v2 dp
                                  JOIN draft_pokemon_v2 pp
                                       ON dp.draft_id = pp.draft_id
                         GROUP BY LOWER(dp.player_name), pp.pokemon)
                SELECT a.drafted_by, \
                       a.pokemon, \
                       COALESCE(s.times_drafted, 0)                                    AS times_drafted, \
                       a.times_available, \
                       CAST(COALESCE(s.times_drafted, 0) AS FLOAT) / a.times_available AS percent_drafted
                FROM pokemon_available a
                         LEFT JOIN player_stats s
                                   ON a.drafted_by = s.drafted_by
                                       AND a.pokemon = s.pokemon
                WHERE a.times_available >= 3
                ORDER BY a.drafted_by, percent_drafted DESC \
                """

    # --------------------
    # Load data
    # --------------------
    df_signature = pd.read_sql_query(SQL_QUERY, conn)

    st.write(df_signature)

    # Only show signature picks >= 60%
    df_signature = df_signature[df_signature["percent_drafted"] >= 0.6]

    # --------------------
    # Player selector
    # --------------------
    players = sorted(df_signature["drafted_by"].unique())
    selected_player = st.selectbox("Select a Player", players)

    df_player = df_signature[df_signature["drafted_by"] == selected_player].copy()


    # Add a category for coloring
    def pick_type(row):
        if row["percent_drafted"] >= 0.8:
            return "Super Signature"
        else:
            return "Signature"

    

    df_player["pick_type"] = df_player.apply(pick_type, axis=1)

    # --------------------
    # Bar chart
    # --------------------
    color_scale = alt.Scale(domain=["Signature", "Super Signature"], range=["#9999FF", "#FF3333"])

    signature_chart = alt.Chart(df_player).mark_bar().encode(
        x=alt.X('pokemon:N', sort=df_player['pokemon'].tolist(), title="Pokémon",
        axis=alt.Axis(
            labelFontWeight="bold",
            labelFontSize=16,
            labelAngle=-60,
            titleFontWeight="bold",
            titleFontSize=18
        )),
        y=alt.Y('percent_drafted:Q', title="Draft Rate",
        axis=alt.Axis(
            format=".0%",
            titleFontWeight="bold",
            titleFontSize=18
        )),
        color=alt.Color('pick_type:N', scale=color_scale, legend=alt.Legend(title="Pick Type")),
        tooltip=['pokemon',
                 'times_drafted',
                 'times_available',
                 alt.Tooltip('percent_drafted:Q', format=".2%"),
                 'pick_type']
    ).properties(
        width=800,
        height=400,
        title=f"Signature Pokémon for {selected_player.title()}"
    )

    st.altair_chart(signature_chart)


    st.write("Charts coming soon:")
    st.write("- Pokémon drafted per patch")
    st.write("- Average spend per patch")
    st.write("- Signature Pokémon")

    st.header("Player Draft Value vs Global Average (All Patches)")
    st.write("This graph shows the top 10 largest differences between what a player pays and what the average"
             "price of each Pokemon is across all drafts. The player must have drafted the Pokemon at least 2 times.")

    SQL_QUERY = """
                WITH global_avg AS (
                SELECT
                    pokemon,
                    AVG(cost) AS global_avg_cost
                FROM draft_pokemon_v2
                GROUP BY pokemon
            ),
            player_stats AS (
                SELECT
                    pokemon,
                    LOWER(drafted_by) AS drafted_by,
                    AVG(cost) AS player_avg_cost,
                    COUNT(*) AS times_drafted
                FROM draft_pokemon_v2
                GROUP BY pokemon, LOWER(drafted_by)
            ),
            eligible_players AS (
                SELECT drafted_by
                FROM player_stats
                WHERE times_drafted >= 2
                GROUP BY drafted_by
                HAVING COUNT(*) >= 3
            )
            SELECT
                p.pokemon,
                p.drafted_by,
                p.player_avg_cost,
                g.global_avg_cost,
                p.times_drafted,
                (p.player_avg_cost - g.global_avg_cost) AS delta
            FROM player_stats p
            JOIN global_avg g
                ON p.pokemon = g.pokemon
            JOIN eligible_players e
                ON p.drafted_by = e.drafted_by
            WHERE p.times_drafted >= 2
                """

    df_player_compare = pd.read_sql_query(SQL_QUERY, conn)

    players = sorted(df_player_compare["drafted_by"].unique())
    selected_player = st.selectbox("Select a Player", players)

    df_player = df_player_compare[
        df_player_compare["drafted_by"] == selected_player
        ].copy()

    # --- NEW: keep only top 10 most impactful Pokémon ---
    df_player["abs_delta"] = df_player["delta"].abs()

    df_player = (
        df_player
        .sort_values("abs_delta", ascending=False)
        .head(10)
    )

    # Re-sort for diverging bar chart display
    df_player = df_player.sort_values("delta")

    chart = alt.Chart(df_player).mark_bar().encode(
        x=alt.X("pokemon:N", sort=df_player["pokemon"].tolist(),
                title="Pokémon",
                axis=alt.Axis(
                    labelFontWeight="bold",
                    labelFontSize=16,
                    labelAngle=-60,
                    titleFontWeight = "bold",
                    titleFontSize = 18
                )
                ),
        y=alt.Y("delta:Q", title="Cost vs Global Average",
                axis=alt.Axis(
                    titleFontWeight="bold",
                    titleFontSize=18
                )),
        color=alt.condition(
            alt.datum.delta > 0,
            alt.value("#E45756"),
            alt.value("#4C78A8")
        ),
        tooltip=[
            "pokemon",
            alt.Tooltip("player_avg_cost:Q", title="Player Avg Cost", format=",.0f"),
            alt.Tooltip("global_avg_cost:Q", title="Global Avg Cost", format=",.0f"),
            alt.Tooltip("delta:Q", title="Difference", format="+,.0f"),
            alt.Tooltip("times_drafted:Q", title="Times Drafted")
        ]
    ).properties(
        width=1000,
        height=400,
        title=f"{selected_player}: Draft Behavior vs Global Average"
    )

    zero_line = alt.Chart(
        pd.DataFrame({"y": [0]})
    ).mark_rule(color="black").encode(y="y:Q")

    st.altair_chart(chart + zero_line, use_container_width=True)



#appendix tab
with tab_appendix:
    st.header("Appendix: Raw Database Tables")

    st.markdown("""
    This appendix contains **all raw tables used in this dashboard**.

    These tables are **free to use** for your own analysis, visualizations, or external tools.
    You can:
    - Sort columns
    - Copy rows
    - Export data for your own projects

    If you build something cool, feel free to share it with the community!
    """)

    st.divider()

    # --------------------
    # draft_event_v2
    # --------------------
    st.subheader("draft_event_v2")
    st.caption("One row per draft event (draft metadata such as date, patch, totals).")

    df_draft_event = pd.read_sql_query(
        "SELECT * FROM draft_event_v2",
        conn
    )

    st.dataframe(
        df_draft_event,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------
    # draft_players_v2
    # --------------------
    st.subheader("draft_players_v2")
    st.caption("One row per player per draft.")

    df_draft_players = pd.read_sql_query(
        "SELECT * FROM draft_players_v2",
        conn
    )

    st.dataframe(
        df_draft_players,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------
    # draft_pokemon_v2
    # --------------------
    st.subheader("draft_pokemon_v2")
    st.caption("One row per Pokémon pick (includes cost, draft order, and player).")

    df_draft_pokemon = pd.read_sql_query(
        "SELECT * FROM draft_pokemon_v2",
        conn
    )

    st.dataframe(
        df_draft_pokemon,
        use_container_width=True,
        hide_index=True
    )



# # Load top 3 Pokémon per draft
# df_top3 = pd.read_sql_query("SELECT * FROM vw_top3_pokemon_per_draft;", conn)
#
#
# st.header("Top 3 Most Expensive Pokémon per Draft")
# st.write("This chart shows the top 3 most expensive Pokémon for each draft.")
#
# top3_chart = alt.Chart(df_top3).mark_bar().encode(
#     x='pokemon:N',               # Pokémon names on x-axis
#     y='cost:Q',                  # Cost on y-axis
#     color='draft_id:N',          # Different color for each draft
#     tooltip=['draft_id', 'pokemon', 'drafted_by', 'cost', 'draft_order']  # hover info
# ).properties(width=700)
#
# st.altair_chart(top3_chart)



