import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
from scipy.stats import rankdata

# Custom CSS for blue sidebar
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #004080;
        }
        .sidebar .sidebar-content {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# Load and combine data
df = pd.read_excel("gps_data2.xlsx", sheet_name=None)
df = pd.concat(df.values(), ignore_index=True)

# Sidebar
st.sidebar.header("⚙️ Please Filter Here")

selected_games = st.sidebar.multiselect("Select Game(s)", df["Game"].unique(), default=df["Game"].unique())
filtered_df = df[df["Game"].isin(selected_games)]

positions = filtered_df["Position"].dropna().unique()
selected_positions = st.sidebar.multiselect("Select Position(s)", positions, default=positions)
position_filtered_df = filtered_df[filtered_df["Position"].isin(selected_positions)]

players = position_filtered_df["name"].unique()
selected_players = st.sidebar.multiselect("Select Player(s)", players, default=[])

chart_type = st.sidebar.selectbox(
    "Select Chart Type",
    ["None", "Line Chart", "Pie Chart", "Pizza Chart"]
)

if selected_players:
    final_df = position_filtered_df[position_filtered_df["name"].isin(selected_players)]
else:
    final_df = position_filtered_df

# Main Title
st.title(":bar_chart: GPS Data Dashboard")
st.markdown("##")

# KPI
total_distance = final_df["Distance"].sum()
total_sprint = final_df["Sprint Distance"].sum()
hi_distance = final_df["HI Distance"].sum()
average_distance = round(filtered_df["Distance"].mean(), 1)

if selected_players:
    st.subheader(f"📍 KPIs for Player(s): {', '.join(selected_players)}")
elif selected_positions:
    st.subheader(f"📍 KPIs for Position(s): {', '.join(selected_positions)}")
else:
    st.subheader("📍 KPIs for Entire Team")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Distance", f"{total_distance:.1f} M")
col2.metric("Average Team Distance", f"{average_distance:.1f} M")
col3.metric("Sprint Distance", f"{total_sprint:.1f} M")
col4.metric("HI Distance", f"{hi_distance:.1f} M")

# ---- LINE CHART ----
if chart_type == "Line Chart" and selected_players:
    st.markdown("## 📈 Line Trend Charts")

    for player in selected_players:
        player_df = df[df["name"] == player].sort_values(by="Game")
        player_df = player_df.tail(5)

        if player_df.empty:
            st.warning(f"No data for {player}")
            continue

        st.markdown(f"### {player}")

        metrics = {
            "Total Distance": ("Distance", '#1f77b4'),
            "Running Distance": ("Running Distance", '#2ca02c'),
            "HI Distance": ("HI Distance", '#ff7f0e'),
            "HS Distance": ("HS Distance", '#9467bd'),
            "Sprint Distance": ("Sprint Distance", '#d62728')
        }

        for title, (column, color) in metrics.items():
            if column not in player_df.columns or player_df[column].dropna().empty:
                continue

            fig, ax = plt.subplots(figsize=(6, 3))
            ax.plot(player_df["Game"], player_df[column], marker='o', linestyle='-', color=color, label=title)
            ax.set_title(f"{title}")
            ax.set_xlabel("Game")
            ax.set_ylabel("Distance (M)")
            ax.grid(True)
            ax.legend()
            plt.xticks(rotation=45)
            st.pyplot(fig)

# ---- PIE CHART ----
if chart_type == "Pie Chart" and selected_players:
    st.markdown("## 🥧 Pie Chart: Game-by-Game Distance Breakdown")

    colors = {
        "Running Distance": '#2ca02c',
        "HI Distance": '#ff7f0e',
        "HS Distance": '#9467bd',
        "Sprint Distance": '#d62728'
    }

    for player in selected_players:
        player_df = df[df["name"] == player].sort_values(by="Game")
        player_df = player_df.tail(5)

        if player_df.empty:
            st.warning(f"No data for pie chart: {player}")
            continue

        st.markdown(f"### {player}")

        for _, row in player_df.iterrows():
            game = row["Game"]
            total = row.get("Distance", 0)

            if total == 0 or pd.isna(total):
                st.warning(f"Skipping {game} for {player}")
                continue

            values = {
                "Running Distance": row.get("Running Distance", 0),
                "HI Distance": row.get("HI Distance", 0),
                "HS Distance": row.get("HS Distance", 0),
                "Sprint Distance": row.get("Sprint Distance", 0)
            }

            labels = list(values.keys())
            sizes = [(v / total) * 100 if total > 0 else 0 for v in values.values()]
            slice_colors = [colors[label] for label in labels]

            fig, ax = plt.subplots()
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=slice_colors,
                autopct='%1.1f%%',
                startangle=90,
                textprops=dict(color="white", fontsize=12)
            )
            ax.set_title(f"{player} - {game}")
            ax.axis('equal')
            ax.legend(wedges, labels, title="Distance Types", loc="center left", bbox_to_anchor=(1, 0.5))
            st.pyplot(fig)

# ---- PIZZA CHART ----
def draw_pizza_chart(player_name, player_data, all_data, title):
    categories = player_data.index.tolist()
    percentiles = []

    for metric in categories:
        values = all_data[metric].values
        ranks = rankdata(values, method="average")
        percentile = (ranks[all_data.index.get_loc(player_name)] - 1) / (len(values) - 1) * 100 if len(values) > 1 else 100
        percentiles.append(percentile)

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    percentiles += percentiles[:1]
    angles += angles[:1]

    ax.plot(angles, percentiles, color="#1f77b4", linewidth=2, linestyle='solid')
    ax.fill(angles, percentiles, color="#1f77b4", alpha=0.4)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories)
    ax.set_ylim(0, 100)
    ax.set_title(title, fontsize=14, pad=20)

    for angle, value in zip(angles, percentiles):
        ax.text(angle, value + 4, f"{int(value)}%", ha='center', va='center', fontsize=10, color="#1f77b4")

    ax.grid(True)
    st.pyplot(fig)

if chart_type == "Pizza Chart" and selected_players:
    st.markdown("## 🍕 Pizza Charts: Percentile Comparison")

    pizza_metrics = ["Running Distance", "HS Distance", "HI Distance", "Sprint Distance", "Distance"]

    # Cumulative data
    player_totals = filtered_df.groupby(["name", "Position"])[pizza_metrics].sum().reset_index()
    player_totals.set_index("name", inplace=True)

    # Chart 1: Compare within same position
    st.subheader("🔵 Pizza Chart 1: Percentiles vs Players in Same Position")
    for player in selected_players:
        if player not in player_totals.index:
            st.warning(f"No data for {player}")
            continue

        pos = player_totals.loc[player, "Position"]
        same_pos_df = player_totals[player_totals["Position"] == pos]
        draw_pizza_chart(player, same_pos_df.loc[player, pizza_metrics], same_pos_df[pizza_metrics], f"{player} vs {pos}s")

    # Chart 2: Compare to all players
    st.subheader("🔵 Pizza Chart 2: Percentiles vs All Players")
    for player in selected_players:
        if player not in player_totals.index:
            continue
        draw_pizza_chart(player, player_totals.loc[player, pizza_metrics], player_totals[pizza_metrics], f"{player} vs All Players")
