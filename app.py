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
if "tab" not in st.session_state:
    st.session_state.tab = TABS[0]
tab = st.sidebar.radio("Select Page", TABS, index=TABS.index(st.session_state.tab))

# Helper to get stat min/max for sliders
def get_stat_range(stat):
    q = f"SELECT MIN({stat}), MAX({stat}) FROM cards"
    mn, mx = conn.execute(q).fetchone()
    return int(mn or 0), int(mx or 100)

if tab == "Card Table":
    st.session_state.tab = "Card Table"
    # Sidebar filters
    player_search = st.sidebar.text_input("Search player name (partial)", "")
    team = st.sidebar.multiselect("Team", get_options("teamname"), default=None)
    league = st.sidebar.multiselect("League", get_options("league"), default=None)
    year = st.sidebar.multiselect("Year", [str(y) for y in get_options("year")], default=None)
    split = st.sidebar.multiselect("Split", get_options("split"), default=None)
    card_class = st.sidebar.multiselect("Class", get_options("class"), default=None)
    position = st.sidebar.multiselect("Position", get_options("position"), default=None)
    # Stat range sliders
    stat_filters = {}
    for stat in ['final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency']:
        mn, mx = get_stat_range(stat)
        stat_filters[stat] = st.sidebar.slider(f"{stat.replace('final_','').capitalize()} range", mn, mx, (mn, mx))

    # Build query dynamically
    query = "SELECT * FROM cards WHERE 1=1"
    params = []
    if player_search:
        query += " AND playername LIKE ?"
        params.append(f"%{player_search}%")
    if team:
        query += f" AND teamname IN ({','.join(['?']*len(team))})"
        params.extend(team)
    if league:
        query += f" AND league IN ({','.join(['?']*len(league))})"
        params.extend(league)
    if year:
        query += f" AND year IN ({','.join(['?']*len(year))})"
        params.extend([int(y) for y in year])
    if split:
        query += f" AND split IN ({','.join(['?']*len(split))})"
        params.extend(split)
    if card_class:
        query += f" AND class IN ({','.join(['?']*len(card_class))})"
        params.extend(card_class)
    if position:
        query += f" AND position IN ({','.join(['?']*len(position))})"
        params.extend(position)
    for stat, (mn, mx) in stat_filters.items():
        query += f" AND {stat} BETWEEN ? AND ?"
        params.extend([mn, mx])
    query += " ORDER BY league, year, split, teamname, playername"

    cards_df = pd.read_sql_query(query, conn, params=params)

    if cards_df.empty:
        st.warning("No cards found for the selected filters.")
    else:
        # Show only relevant columns, round stats
        display_cols = [
            'id', 'playername', 'teamname', 'position', 'league', 'season', 'year', 'split', 'class',
            'final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency'
        ]
        for stat in ['final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency']:
            if stat in cards_df:
                cards_df[stat] = cards_df[stat].round(0).astype(int)
        # Sorting
        sort_col = st.selectbox("Sort by", display_cols, index=1)
        sort_asc = st.checkbox("Ascending", value=True)
        cards_df = cards_df.sort_values(by=sort_col, ascending=sort_asc)
        # Pagination
        page_size = st.selectbox("Rows per page", [10, 25, 50, 100], index=1)
        page_num = st.number_input("Page", min_value=1, max_value=max(1, (len(cards_df)-1)//page_size+1), value=1)
        start = (page_num-1)*page_size
        end = start+page_size
        paged_df = cards_df.iloc[start:end]
        # Clickable rows (use id as unique key)
        st.write("Click a row to preview the card:")
        id_to_label = lambda row: f"{row['playername']} ({row['teamname']}, {row['season']})"
        selected_id = st.radio(
            "Select a card to preview",
            paged_df['id'],
            format_func=lambda i: id_to_label(paged_df[paged_df['id'] == i].iloc[0]),
            key="card_table_radio"
        )
        st.dataframe(paged_df[display_cols], use_container_width=True)
        if st.button("Preview selected card"):
            st.session_state.selected_card_id = selected_id
            st.session_state.tab = "Admin Card Preview"
            st.session_state.just_navigated = True
            st.experimental_rerun()

elif tab == "Admin Card Preview":
    st.session_state.tab = "Admin Card Preview"
    st.header("Admin Card Preview")
    all_cards = pd.read_sql_query("SELECT * FROM cards ORDER BY league, year, split, teamname, playername", conn)
    id_to_label = lambda row: f"{row['playername']} ({row['teamname']}, {row['season']})"
    # Navigation logic
    if "selected_card_id" in st.session_state and st.session_state.selected_card_id in all_cards['id'].values:
        default_id = st.session_state.selected_card_id
    else:
        default_id = all_cards['id'].iloc[0]
    # Only set index if just navigated
    if st.session_state.get("just_navigated", False):
        selectbox_index = all_cards['id'].tolist().index(default_id) if default_id in all_cards['id'].tolist() else 0
        st.session_state.just_navigated = False
    else:
        selectbox_index = None
    card_id = st.sidebar.selectbox(
        "Select card",
        all_cards['id'],
        format_func=lambda i: id_to_label(all_cards[all_cards['id'] == i].iloc[0]),
        index=selectbox_index if selectbox_index is not None else 0,
        key="admin_card_selectbox"
    )
    st.session_state.selected_card_id = card_id
    card = all_cards[all_cards['id'] == card_id].iloc[0]

    # Background selection
    bg_dir = "static/backgrounds"
    bg_files = [f for f in os.listdir(bg_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    bg_file = st.sidebar.selectbox("Select background", bg_files)
    bg_path = f"/app/static/backgrounds/{bg_file}"
    player_img = "/app/static/player_images/placeholder_profile.jpg"
    team_img_svg = "/app/static/team_logos/t1_esports_logo.svg"
    team_img_png = "/app/static/team_logos/t1_esports_logo.png"
    class_img = "/app/static/class_icons/placeholder_class.webp"
    overall = int(round((card['final_offense'] + card['final_defense'] + card['final_utility'] + card['final_macro'] + card['final_clutch'] + card['final_consistency']) / 6))
    position_label = card['position'].upper() if isinstance(card['position'], str) else card['position']
    stat_labels = [
        ("ATT", int(round(card['final_offense']))),
        ("DEF", int(round(card['final_defense']))),
        ("UTL", int(round(card['final_utility']))),
        ("MAC", int(round(card['final_macro']))),
        ("CLT", int(round(card['final_clutch']))),
        ("STB", int(round(card['final_consistency'])))
    ]
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