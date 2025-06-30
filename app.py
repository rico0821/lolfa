import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="LoL eSports Player Card", layout="wide")
st.title("LoL eSports Player Card")

db_path = "stat_cards.db"
conn = sqlite3.connect(db_path)

# Helper to get unique options for a column
@st.cache_data
def get_options(col):
    return [row[0] for row in conn.execute(f"SELECT DISTINCT {col} FROM cards ORDER BY {col}").fetchall() if row[0] not in (None, '')]

# Tabs: Main (table) and Admin Card Preview
TABS = ["Card Table", "Admin Card Preview"]
tab = st.sidebar.radio("Select Page", TABS)

if tab == "Card Table":
    # Sidebar filters
    player_search = st.sidebar.text_input("Search player name (partial)", "")
    team = st.sidebar.selectbox("Team", ["All"] + get_options("teamname"))
    league = st.sidebar.selectbox("League", ["All"] + get_options("league"))
    year = st.sidebar.selectbox("Year", ["All"] + [str(y) for y in get_options("year")])
    split = st.sidebar.selectbox("Split", ["All"] + get_options("split"))
    card_class = st.sidebar.selectbox("Class", ["All"] + get_options("class"))

    # Build query dynamically
    query = "SELECT * FROM cards WHERE 1=1"
    params = []
    if player_search:
        query += " AND playername LIKE ?"
        params.append(f"%{player_search}%")
    if team != "All":
        query += " AND teamname = ?"
        params.append(team)
    if league != "All":
        query += " AND league = ?"
        params.append(league)
    if year != "All":
        query += " AND year = ?"
        params.append(int(year))
    if split != "All":
        query += " AND split = ?"
        params.append(split)
    if card_class != "All":
        query += " AND class = ?"
        params.append(card_class)
    query += " ORDER BY league, year, split, teamname, playername"

    cards_df = pd.read_sql_query(query, conn, params=params)

    if cards_df.empty:
        st.warning("No cards found for the selected filters.")
    else:
        # Show only relevant columns, round stats
        display_cols = [
            'playername', 'teamname', 'league', 'season', 'year', 'split', 'class',
            'final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency'
        ]
        for stat in ['final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency']:
            if stat in cards_df:
                cards_df[stat] = cards_df[stat].round(0).astype(int)
        st.dataframe(cards_df[display_cols], use_container_width=True)

elif tab == "Admin Card Preview":
    st.header("Admin Card Preview")
    # Card selection
    all_cards = pd.read_sql_query("SELECT * FROM cards ORDER BY league, year, split, teamname, playername", conn)
    card_idx = st.sidebar.selectbox("Select card", all_cards.index, format_func=lambda i: f"{all_cards.loc[i, 'playername']} ({all_cards.loc[i, 'teamname']}, {all_cards.loc[i, 'season']})")
    card = all_cards.loc[card_idx]

    # Background selection
    bg_dir = "static/backgrounds"
    bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    bg_file = st.sidebar.selectbox("Select background", bg_files)

    # Background path for HTML (must be /app/static/...)
    bg_path = f"/app/static/backgrounds/{bg_file}"

    # Use local static images for placeholders (served via /app/static/ path)
    player_img = "/app/static/player_images/placeholder_profile.jpg"
    team_img_svg = "/app/static/team_logos/t1_esports_logo.svg"
    team_img_png = "/app/static/team_logos/t1_esports_logo.png"  # fallback if you add a PNG version
    class_img = "/app/static/class_icons/placeholder_class.webp"

    # Card rendering (HTML/CSS) with improved fitting, alt attributes, and spacing
    overall = int(round((card['final_offense'] + card['final_defense'] + card['final_utility'] + card['final_macro'] + card['final_clutch'] + card['final_consistency']) / 6))
    # Capitalize all letters of the position for display
    position_label = card['position'].upper() if isinstance(card['position'], str) else card['position']
    # Stat label abbreviations
    stat_labels = [
        ("ATT", int(round(card['final_offense']))),
        ("DEF", int(round(card['final_defense']))),
        ("UTL", int(round(card['final_utility']))),
        ("MAC", int(round(card['final_macro']))),
        ("CLT", int(round(card['final_clutch']))),
        ("STB", int(round(card['final_consistency'])))
    ]
    # Prepare two-column stats layout
    stat_pairs = list(zip(stat_labels[:3], stat_labels[3:]))
    card_html = f'''
    <div style="position:relative;width:340px;height:540px;background:url('{bg_path}');background-size:cover;background-position:center;border-radius:32px;margin:auto;overflow:hidden;">
      <div style="position:absolute;inset:0;background:rgba(0,0,0,0.18);"></div>
      <div style="position:absolute;top:64px;left:20px;width:64px;height:64px;display:flex;align-items:center;justify-content:center;font-size:44px;font-weight:bold;color:#444;text-shadow:2px 2px 8px #fff2;z-index:2;">{overall}</div>
      <img src="{class_img}" alt="Class Icon" style="position:absolute;top:132px;left:52px;transform:translateX(-50%);width:36px;height:36px;background:none;border-radius:8px;z-index:2;" />
      <div style="position:absolute;top:132px;left:0;width:100%;text-align:center;font-size:1.2rem;font-weight:600;color:#ffe;text-shadow:1px 1px 4px #000;z-index:2;">{position_label}</div>
      <img src="{team_img_svg}" onerror="this.onerror=null;this.src='{team_img_png}'" alt="Team Logo" style="position:absolute;top:74px;right:20px;height:36px;width:auto;object-fit:contain;z-index:2;background:#fff2;border-radius:12px;padding:4px;">
      <img src="{player_img}" alt="Player" style="position:absolute;top:170px;left:50%;transform:translateX(-50%);width:96px;height:96px;object-fit:cover;border-radius:50%;border:3px solid #fff8;z-index:2;background:#2228;">
      <div style="position:absolute;top:270px;left:0;width:100%;text-align:center;font-size:1.3rem;font-weight:600;color:#fff;text-shadow:1px 1px 4px #000;z-index:2;">{card['playername']}</div>
      <div style='height:12px;'></div>
      <div style="position:absolute;top:300px;left:0;width:100%;text-align:center;font-size:1.1rem;color:#fff;text-shadow:1px 1px 4px #000;z-index:2;">{card['teamname']} | {card['league']} | {card['season']}</div>
      <div style="position:absolute;top:340px;left:0;width:100%;z-index:2;display:flex;flex-direction:column;align-items:center;gap:2px;">
        <div style='margin-top:12px;display:flex;flex-direction:row;justify-content:center;width:80%;gap:8px;'>
          <div style='flex:1;display:flex;flex-direction:column;gap:2px;'>
            {''.join([f'<div style="display:flex;justify-content:space-between;font-size:1.05rem;color:#fff;background:rgba(0,0,0,0.32);border-radius:8px;padding:2px 8px;">{l[0]}<span>{l[1]}</span></div>' for l in [pair[0] for pair in stat_pairs]])}
          </div>
          <div style='flex:1;display:flex;flex-direction:column;gap:2px;'>
            {''.join([f'<div style="display:flex;justify-content:space-between;font-size:1.05rem;color:#fff;background:rgba(0,0,0,0.32);border-radius:8px;padding:2px 8px;">{l[0]}<span>{l[1]}</span></div>' for l in [pair[1] for pair in stat_pairs]])}
          </div>
        </div>
      </div>
    </div>
    '''
    st.markdown(card_html, unsafe_allow_html=True)