import streamlit as st
import pandas as pd
import sqlite3
import altair as alt
import os
import base64
from pathlib import Path

# --------------------
# Configuration
# --------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "PokemonDraftData.db")

# Connect to SQLite database
conn = sqlite3.connect(DB_PATH)


POKEMON_IMAGE_DIR = "assets/baseforms"

logo_path = Path("assets/blitzlogo.png")

st.set_page_config(page_title="Pokemon Blitz Data Dashboard")

def get_pokemon_image(pokemon_name: str) -> str | None:
    base_path = Path("assets/baseforms")
    img_path = base_path / f"{pokemon_name}.png"

    if not img_path.exists():
        return None

    with open(img_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:image/png;base64,{encoded}"



def image_to_base64(path):
    if not path or not Path(path).exists():
        return None

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"

def add_pokemon_images(
    base_chart: alt.Chart,
    df: pd.DataFrame,
    *,
    image_size: int = 40,
    y_offset: float = 0,
):
    """
    Adds Pokémon images aligned to the x-axis categories of a bar chart.
    """

    image_chart = alt.Chart(df).mark_image(
        width=image_size,
        height=image_size
    ).encode(
        x=alt.X(
            'pokemon:N',
            sort=df['pokemon'].tolist()
        ),
        y=alt.value(y_offset),
        url='image:N',
        tooltip=[
            alt.Tooltip('pokemon:N', title='Pokémon')
        ]
    )

    return base_chart + image_chart

def remove_price_outliers_per_pokemon(df, value_col="cost", group_col="pokemon", k=2.0, j=1.5):
    df[value_col] = pd.to_numeric(df[value_col], errors='coerce')  # force numeric

    def filter_group(group):
        q1 = group[value_col].quantile(0.25)
        q3 = group[value_col].quantile(0.75)
        iqr = q3 - q1

        lower = q1 - j * iqr
        upper = q3 + k * iqr

        return group[(group[value_col] >= lower) & (group[value_col] <= upper)]

    return df.groupby(group_col, group_keys=False).apply(filter_group)


tab_welcome, tab_game_stats, tab_global, tab_players, tab_appendix = st.tabs([
    "Welcome",
    "Overall Game Stats",
    "All Draft Data",
    "Player Data",
    "Appendix"
])

#Add all information for Welcome tab here

with tab_welcome:

    bg_image = image_to_base64(logo_path)

    st.markdown(
        f"""
        <style>
        .hero {{
            width: 100%;
            height: 60vh;
            background-image: url("{bg_image}");
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            position: relative;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 40px;
        }}

        .hero-text {{
            font-size: 2.2rem;
            font-weight: 700;
            color: white;
            text-align: center;
            text-shadow:
                0 2px 4px rgba(0,0,0,0.8),
                0 4px 12px rgba(0,0,0,0.6);
        }}
        </style>

        <div class="hero">
            <div class="hero-text">
                Welcome to the <strong>Pokémon Emerald Blitz Draft Dashboard</strong>!
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # st.title("Pokémon Emerald Blitz Dashboard")


    st.markdown("""

    This dashboard provides insights into:
    - Draft trends across all time
    - How patches affect the meta
    - Player behavior and preferences
    - Full access to the underlying data
    """)


    st.subheader("Links")
    st.markdown("""
    - 💬 [Discord](https://discord.com/invite/CsUSZ5UhzW)
    - Full Draft Website (https://auction.emeraldblitz.workers.dev)
    - 📊 GitHub Repository (https://github.com/Mfrazz/pokemon-emerald-blitz-dashboard)
    """)

    st.info("Use the tabs above to explore the data.")

with tab_game_stats:
    # --------------------
    # Overall Game Stats Tab
    # --------------------
    st.header("Overall Game Stats")
    st.markdown(
        """
        High-level overview of the Pokémon Emerald Blitz game.
        \n(Work in Progress)
        """
    )

    # --------------------
    # Total unique players
    # --------------------
    total_players = pd.read_sql_query(
        "SELECT COUNT(DISTINCT player_name) AS total_players FROM draft_players_v2",
        conn
    )["total_players"].iloc[0]

    # --------------------
    # Total Pokémon drafted
    # --------------------
    total_pokemon_drafted = pd.read_sql_query(
        "SELECT COUNT(*) AS total_drafted FROM draft_pokemon_v2",
        conn
    )["total_drafted"].iloc[0]

    # --------------------
    # Drafts per day
    # --------------------
    drafts_per_day = pd.read_sql_query(
        """
        SELECT date (date_time) AS draft_date, COUNT (*) AS drafts_count
        FROM draft_event_v2
        GROUP BY draft_date
        ORDER BY draft_date
        """,
        conn
    )

    avg_drafts_per_day = drafts_per_day["drafts_count"].mean()

    # --------------------
    # Player with most drafts in a single day
    # --------------------
    most_drafts_day = pd.read_sql_query(
        """
        SELECT dp.player_name, date (de.date_time) AS draft_date, COUNT (*) AS drafts_count
        FROM draft_players_v2 dp
            JOIN draft_event_v2 de
        ON dp.draft_id = de.id
        GROUP BY dp.player_name, draft_date
        ORDER BY drafts_count DESC
            LIMIT 1
        """,
        conn
    )

    # --------------------
    # Display metrics
    # --------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Unique Players", total_players)
    col2.metric("Total Pokémon Drafted", total_pokemon_drafted)
    col3.metric("Average Drafts Per Day", f"{avg_drafts_per_day:.2f}")

    st.markdown("---")

    st.subheader("Record Drafts in a Single Day")
    st.write(
        f"{most_drafts_day.iloc[0]['player_name']} drafted "
        f"{most_drafts_day.iloc[0]['drafts_count']} times on {most_drafts_day.iloc[0]['draft_date']}"
    )

    # --------------------
    # Longest Streak of Drafts (at least 1 draft/day)
    # --------------------
    # Query all draft dates per player
    draft_dates = pd.read_sql_query(
        """
        SELECT dp.player_name, date (de.date_time) AS draft_date
        FROM draft_players_v2 dp
            JOIN draft_event_v2 de
        ON dp.draft_id = de.id
        GROUP BY dp.player_name, draft_date
        ORDER BY dp.player_name, draft_date
        """,
        conn
    )


    # Function to calculate the longest streak per player
    def longest_streak(dates):
        dates = pd.to_datetime(dates).sort_values()
        streaks = []
        current_streak = 1
        for i in range(1, len(dates)):
            if (dates.iloc[i] - dates.iloc[i - 1]).days == 1:
                current_streak += 1
            else:
                streaks.append(current_streak)
                current_streak = 1
        streaks.append(current_streak)
        return max(streaks)


    # Calculate longest streaks per player
    streaks = (
        draft_dates.groupby("player_name")["draft_date"]
        .apply(longest_streak)
        .reset_index(name="longest_streak")
        .sort_values("longest_streak", ascending=False)
    )

    st.subheader("Longest Draft Streaks (1 draft/day)")
    st.dataframe(streaks.head(10), use_container_width=True)

#tab for all data across all patches

with tab_global:
    st.header("Patch-Based Draft Trends")
    st.markdown("Analyze how draft behavior changes between patches.")

    # --------------------
    # Get patches once
    # --------------------
    patches = pd.read_sql_query("SELECT DISTINCT patch FROM draft_event_v2 ORDER BY patch", conn)["patch"].tolist()
    patch_options = ["All Patches"] + patches

    # --------------------
    # Average Cost per Pokémon by Patch
    # --------------------
    st.header("Average Cost per Pokémon by Patch")
    st.write("Shows the average draft price of each Pokémon and how often it was drafted, filtered by patch.")
    st.write("*Note* Outliers have been removed from Avg Cost Views")

    selected_patch_cost_chart = st.selectbox("Select Patch for Average Cost Chart", patch_options, key="avg_cost_patch")

    # Build WHERE clause for SQL
    where_clause = ""
    params = []
    if selected_patch_cost_chart != "All Patches":
        where_clause = "WHERE de.patch = ?"
        params.append(selected_patch_cost_chart)

    # Query Pokémon cost data
    df_raw = pd.read_sql_query(f"""
        SELECT
            dp.pokemon,
            dp.cost
        FROM draft_pokemon_v2 dp
        JOIN draft_event_v2 de ON dp.draft_id = de.id
        {where_clause}
    """, conn, params=params)

    #removes outliers in average cost dataset
    df_filtered = remove_price_outliers_per_pokemon(df_raw)

    # Top/Bottom selector
    filter_type_patch = st.radio(
        f"Show Top or Bottom Pokémon by Average Cost ({selected_patch_cost_chart})",
        ("Top", "Bottom"),
        key="top_bottom_patch"
    )

    df_avg_pokemon_patch = (
        df_filtered
        .groupby("pokemon")
        .agg(
            avg_cost=("cost", "mean"),
            times_drafted=("cost", "count")
        )
        .reset_index()
    )

    df_avg_pokemon_patch["avg_cost"] = df_avg_pokemon_patch["avg_cost"].round(2)

    x_patch = st.number_input(
        f"How many Pokémon to show for {selected_patch_cost_chart}?",
        min_value=1,
        max_value=len(df_avg_pokemon_patch),
        value=10,
        key="num_patch_pokemon"
    )

    # Sort data based on Top/Bottom selection
    df_avg_pokemon_patch_sorted = df_avg_pokemon_patch.sort_values(
        by="avg_cost",
        ascending=(filter_type_patch == "Bottom")
    )
    df_avg_pokemon_patch_filtered = df_avg_pokemon_patch_sorted.head(x_patch)

    # Altair color scale
    color_scale_patch = alt.Scale(
        domain=[
            df_avg_pokemon_patch_filtered["times_drafted"].min(),
            df_avg_pokemon_patch_filtered["times_drafted"].max()
        ],
        range=["#9999FF", "#000099"]
    )

    # Create bar chart
    avg_pokemon_patch_chart = alt.Chart(df_avg_pokemon_patch_filtered).mark_bar().encode(
        x=alt.X("pokemon:N", sort=df_avg_pokemon_patch_filtered["pokemon"].tolist()),
        y="avg_cost:Q",
        color=alt.Color(
            "times_drafted:Q",
            scale=color_scale_patch,
            legend=alt.Legend(title="Times Drafted")
        ),
        tooltip=["pokemon", "avg_cost", "times_drafted"]
    ).properties(width=1000)

    st.altair_chart(avg_pokemon_patch_chart, use_container_width=True)

    # --------------------
    # Pokémon Price Summary Across Drafts
    # --------------------
    st.subheader("Pokémon Price Summary Across Drafts")

    selected_patch_summary = st.selectbox("Select Patch for Price Summary", patch_options, key="price_summary_patch")

    where_clause_summary = ""
    params_summary = []
    if selected_patch_summary != "All Patches":
        where_clause_summary = "WHERE e.patch = ?"
        params_summary.append(selected_patch_summary)

    SQL_QUERY_POKEMON_PRICE_SUMMARY = f"""
    WITH ranked AS (
        SELECT
            p.pokemon,
            p.cost,
            ROW_NUMBER() OVER (
                PARTITION BY p.pokemon
                ORDER BY p.cost
            ) AS rn,
            COUNT(*) OVER (
                PARTITION BY p.pokemon
            ) AS cnt
        FROM draft_pokemon_v2 p
        JOIN draft_event_v2 e
            ON p.draft_id = e.id
        {where_clause_summary}
    ),
    iqr_calc AS (
        SELECT
            pokemon,
            MAX(CASE WHEN rn = CAST(cnt * 0.25 AS INT) THEN cost END) AS q1,
            MAX(CASE WHEN rn = CAST(cnt * 0.75 AS INT) THEN cost END) AS q3
        FROM ranked
        GROUP BY pokemon
    ),
    filtered AS (
        SELECT
            r.pokemon,
            r.cost
        FROM ranked r
        JOIN iqr_calc i
            ON r.pokemon = i.pokemon
        WHERE
            r.cost BETWEEN
            (i.q1 - 1.5 * (i.q3 - i.q1))
            AND
            (i.q3 + 2.0 * (i.q3 - i.q1))
    )
    SELECT
        pokemon,
        MIN(cost) AS lowest_cost,
        MAX(cost) AS highest_cost,
        MAX(cost) - MIN(cost) AS price_variance,
        COUNT(*) AS times_drafted,
        ROUND(AVG(cost), 2) AS avg_cost
    FROM filtered
    GROUP BY pokemon
    ORDER BY avg_cost DESC
    """


    def avg_cost_color(val):
        if pd.isna(val):
            return ""

        band = int(val // 1000)

        colors = [
            "#9467bd",  # 0–999
            "#1f77b4",  # 1000–1999
            "#2ca02c",  # 2000–2999
            "#ff7f0e",  # 3000–3999
            "#d62728",  # 4000–4999
            "#d62728",  # 5000–5999
            "#d62728",  # 6000–6999
            "#d62728",  # 7000–7999
            "#d62728",  # 8000–8999
            "#d62728",  # 9000+
        ]

        return f"background-color: {colors[min(band, len(colors) - 1)]} "

    df_pokemon_price_summary = pd.read_sql_query(SQL_QUERY_POKEMON_PRICE_SUMMARY, conn, params=params_summary)
    df_pokemon_price_summary = df_pokemon_price_summary.reset_index(drop=True)
    df_pokemon_price_summary.insert(0, "Rank", df_pokemon_price_summary.index + 1)

    styled_df = (
        df_pokemon_price_summary
        .style
        .applymap(avg_cost_color, subset=["avg_cost"])
        .format({
            "avg_cost": "{:,.0f}",
            "lowest_cost": "{:,.0f}",
            "highest_cost": "{:,.0f}",
            "price_variance": "{:,.0f}"
        })
    )


    st.dataframe(styled_df, use_container_width=True, hide_index=True)


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
                    and percent_drafted >= 0.6
                ORDER BY a.drafted_by, percent_drafted DESC \
                """

    # --------------------
    # Load data
    # --------------------
    df_signature = pd.read_sql_query(SQL_QUERY, conn)


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
    # Signature Pokémon Chart with Images
    # --------------------

    # Define color scale
    color_scale = alt.Scale(domain=["Signature", "Super Signature"], range=["#9999FF", "#FF3333"])

    # Ensure each Pokémon has a valid image path
    df_player["image"] = df_player["pokemon"].apply(get_pokemon_image)


    # --------------------
    # Create the Altair bar chart
    # --------------------
    bar_chart = alt.Chart(df_player).mark_bar().encode(
        x=alt.X(
            'pokemon:N',
            sort=df_player['pokemon'].tolist(),
            title="Pokémon",
            axis=alt.Axis(
                labelFontWeight="bold",
                labelFontSize=16,
                labelAngle=-60,
                titleFontWeight="bold",
                titleFontSize=18
            )
        ),
        y=alt.Y(
            'percent_drafted:Q',
            title="Draft Rate",
            axis=alt.Axis(
                format=".0%",
                titleFontWeight="bold",
                titleFontSize=18
            )
        ),
        color=alt.Color(
            'pick_type:N',
            scale=alt.Scale(domain=["Signature", "Super Signature"],
                            range=["#9999FF", "#FF3333"]),
            legend=alt.Legend(title="Pick Type")
        ),
        tooltip=[
            'pokemon',
            'times_drafted',
            'times_available',
            alt.Tooltip('percent_drafted:Q', format=".2%"),
            'pick_type'
        ]
    )

    image_chart = alt.Chart(df_player).mark_image(
        width=40,
        height=40
    ).encode(
        x=alt.X('pokemon:N', sort=df_player['pokemon'].tolist()),
        y=alt.value(0),
        url='image:N',
        tooltip=[
            alt.Tooltip('pokemon:N', title='Pokémon')
        ]
    )

    signature_chart = (
            bar_chart + image_chart
    ).properties(
        height=450,
        title=f"Signature Pokémon for {selected_player.title()}"
    )

    st.altair_chart(signature_chart, use_container_width=True)

    st.header("Signature Pokémon Owners")

    SQL_QUERY_SIGNATURE_OWNERS = SQL_QUERY_SIGNATURE_OWNERS = """
                    WITH player_drafts AS (
                        -- All drafts each player participated in
                        SELECT DISTINCT
                            dp.draft_id,
                            LOWER(dp.player_name) AS drafted_by
                        FROM draft_players_v2 dp
                    ),
                    
                    pokemon_seen AS (
                        -- Pokémon that appeared in drafts a player participated in
                        SELECT DISTINCT
                            pd.draft_id,
                            pl.drafted_by,
                            pd.pokemon
                        FROM draft_pokemon_v2 pd
                        JOIN player_drafts pl
                            ON pd.draft_id = pl.draft_id
                    ),
                    
                    pokemon_available AS (
                        -- Times a Pokémon was available to a specific player
                        SELECT
                            drafted_by,
                            pokemon,
                            COUNT(DISTINCT draft_id) AS times_available
                        FROM pokemon_seen
                        GROUP BY drafted_by, pokemon
                    ),
                    
                    pokemon_drafted AS (
                        -- Times a player drafted a Pokémon (once per draft max)
                        SELECT
                            LOWER(drafted_by) AS drafted_by,
                            pokemon,
                            COUNT(DISTINCT draft_id) AS times_drafted
                        FROM draft_pokemon_v2
                        GROUP BY LOWER(drafted_by), pokemon
                    ),
                    
                    eligible_players AS (
                        -- Players with at least 3 drafts total
                        SELECT
                            LOWER(player_name) AS drafted_by
                        FROM draft_players_v2
                        GROUP BY LOWER(player_name)
                        HAVING COUNT(DISTINCT draft_id) >= 3
                    ),
                    
                    player_rates AS (
                        SELECT
                            a.pokemon,
                            a.drafted_by,
                            COALESCE(d.times_drafted, 0) AS times_drafted,
                            a.times_available,
                            CAST(COALESCE(d.times_drafted, 0) AS FLOAT) / a.times_available AS percent_drafted,
                            (CAST(COALESCE(d.times_drafted, 0) AS FLOAT) / a.times_available)
                                * LOG(COALESCE(d.times_drafted, 0) + 1) AS rating
                        FROM pokemon_available a
                        LEFT JOIN pokemon_drafted d
                            ON a.drafted_by = d.drafted_by
                           AND a.pokemon = d.pokemon
                        JOIN eligible_players e
                            ON a.drafted_by = e.drafted_by
                        WHERE a.times_available >= 3
                          AND COALESCE(d.times_drafted, 0) >= 2
                    ),
                    
                    ranked_players AS (
                        SELECT *,
                               ROW_NUMBER() OVER (
                                   PARTITION BY pokemon
                                   ORDER BY rating DESC
                               ) AS rank_for_pokemon
                        FROM player_rates
                    )
                    
                    SELECT
                        pokemon,
                        drafted_by AS most_likely_player,
                        times_drafted,
                        times_available,
                        percent_drafted,
                        rating
                    FROM ranked_players
                    WHERE rank_for_pokemon = 1
                    ORDER BY rating DESC;
                    """

    df_signature_owners = pd.read_sql_query(SQL_QUERY_SIGNATURE_OWNERS, conn)

    # ---- Formatting for display ----
    df_signature_owners["percent_drafted"] = (
            df_signature_owners["percent_drafted"] * 100
    ).round(2)

    df_signature_owners["rating"] = df_signature_owners["rating"].round(3)

    st.markdown(
        "This table shows **which player is most likely to draft each Pokémon**, "
        "based on both how often they pick it *when available* and how many total "
        "times they’ve drafted it."
    )

    st.dataframe(
        df_signature_owners.rename(columns={
            "pokemon": "Pokémon",
            "most_likely_player": "Most Likely Player",
            "times_drafted": "Times Drafted",
            "times_available": "Times Available",
            "percent_drafted": "Draft Rate (%)",
            "rating": "Signature Rating"
        }),
        use_container_width=True
    )

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

    # Ensure each Pokémon has a valid image path
    df_player["image"] = df_player["pokemon"].apply(get_pokemon_image)



    bar_chart = alt.Chart(df_player).mark_bar().encode(
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

    image_chart = alt.Chart(df_player).mark_image(
        width=40,
        height=40
    ).encode(
        x=alt.X('pokemon:N', sort=df_player['pokemon'].tolist()),
        y=alt.value(0),
        url='image:N',
        tooltip=[
            alt.Tooltip('pokemon:N', title='Pokémon')
        ]
    )

    draft_behavior_chart = (
            bar_chart + image_chart
    ).properties(
        height=450,
        title=f"Signature Pokémon for {selected_player.title()}"
    )

    zero_line = alt.Chart(
        pd.DataFrame({"y": [0]})
    ).mark_rule(color="black").encode(y="y:Q")

    st.altair_chart(draft_behavior_chart + zero_line, use_container_width=True)



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



