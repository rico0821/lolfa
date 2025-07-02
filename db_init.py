import os
import sqlite3
import pandas as pd
import argparse
from stat_card import (
    filter_season_data, generate_final_stat_cards
)
import numpy as np

def create_db(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playername TEXT,
            teamname TEXT,
            position TEXT,
            league TEXT,
            season TEXT,
            year INTEGER,
            split TEXT,
            creation_method TEXT,
            class TEXT,
            final_offense REAL,
            final_defense REAL,
            final_utility REAL,
            final_macro REAL,
            final_clutch REAL,
            final_consistency REAL
        )
    ''')
    conn.commit()
    return conn

def clear_cards_table(conn):
    c = conn.cursor()
    c.execute('DELETE FROM cards')
    conn.commit()

def populate_cards_table(conn, data_dir: str, creation_method: str = 'default', years_to_exclude=None, clear_first=True):
    if years_to_exclude is None:
        years_to_exclude = [2025]
    if clear_first:
        clear_cards_table(conn)
    season_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    df_list = []
    for f in season_files:
        try:
            df_list.append(pd.read_csv(os.path.join(data_dir, f)))
        except Exception as e:
            print(f"[LOG] Error loading {f}: {e}")
    if not df_list:
        print("No data loaded from CSV files.")
        return
    df = pd.concat(df_list, ignore_index=True)
    # Only league games, exclude specified years
    df = df[(df['playoffs'] == 0) & (~df['year'].isin(years_to_exclude))]

    # === NEW: Filter for top leagues (with historic names) ===
    top_leagues = [
        'LCK', 'OGN',
        'LEC', 'EU LCS', 'LCS EU',
        'LCS', 'NA LCS', 'LCS NA'
    ]
    df = df[df['league'].isin(top_leagues)]

    # === NEW: Only use non-partial data ===
    df = df[df['datacompleteness'] != 'partial']

    # === NEW: Infer split from patch if missing ===
    # Build a mapping: (league, year, patch) -> most common split
    patch_split_map = (
        df[df['split'].notnull() & (df['split'].astype(str).str.strip() != '')]
        .groupby(['league', 'year', 'patch'])['split']
        .agg(lambda x: x.value_counts().index[0])
        .to_dict()
    )
    # For rows with missing/empty split, infer from patch
    mask_missing_split = df['split'].isnull() | (df['split'].astype(str).str.strip() == '')
    for idx, row in df[mask_missing_split].iterrows():
        key = (row['league'], row['year'], row['patch'])
        inferred_split = patch_split_map.get(key, None)
        if inferred_split is not None:
            df.at[idx, 'split'] = inferred_split
    # Remove any remaining rows with missing/empty split
    df = df[df['split'].notnull() & (df['split'].astype(str).str.strip() != '')]

    # === NEW: Fill objectives columns with 0 where null/NaN ===
    objective_cols = [
        'dragons', 'opp_dragons',
        'barons', 'opp_barons',
        'heralds', 'opp_heralds',
        'towers', 'opp_towers',
        'void_grubs', 'opp_void_grubs',
        'atakhans', 'opp_atakhans',
        'turretplates'
    ]
    for col in objective_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    for league in df['league'].dropna().unique():
        for year in df['year'].dropna().unique():
            if year in years_to_exclude:
                continue
            for split in df['split'].dropna().unique():
                filtered = filter_season_data(df, league, year, split, playoffs=0)
                if filtered.empty:
                    continue
                try:
                    cards = generate_final_stat_cards(filtered)
                except Exception as e:
                    print(f"[LOG] Error processing {league} {year} {split}: {e}")
                    continue
                cards['league'] = league
                cards['year'] = year
                cards['split'] = split
                cards['season'] = f"{year} {split}"
                cards['creation_method'] = creation_method
                cards['class'] = f"{str(year)[-2:]} LIVE"
                stat_cols = [
                    'final_offense', 'final_defense', 'final_utility',
                    'final_macro', 'final_clutch', 'final_consistency'
                ]
                cards[stat_cols] = cards[stat_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
                cards = cards[['playername', 'teamname', 'position', 'league', 'season', 'year', 'split', 'creation_method', 'class',
                               'final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency']]
                cards.to_sql('cards', conn, if_exists='append', index=False)
                print(f"[LOG] Inserted {len(cards)} cards for {league} {year} {split}")

def update_class_to_year_live(conn):
    """Update 'class' field for all cards to 'YY LIVE' based on year, if class is empty or null."""
    c = conn.cursor()
    c.execute("SELECT id, year FROM cards WHERE class IS NULL OR class = ''")
    updates = [(str(year)[-2:] + ' LIVE', card_id) for card_id, year in c.fetchall()]
    c.executemany("UPDATE cards SET class = ? WHERE id = ?", updates)
    conn.commit()

def main():
    parser = argparse.ArgumentParser(description='Populate the stat_cards.db with LoL eSports player cards.')
    parser.add_argument('--db', type=str, default='stat_cards.db', help='Path to the SQLite database file.')
    parser.add_argument('--data', type=str, default='data', help='Path to the data directory containing CSVs.')
    parser.add_argument('--creation_method', type=str, default='default', help='Creation method label.')
    parser.add_argument('--exclude_years', type=int, nargs='*', default=[2025], help='Years to exclude.')
    parser.add_argument('--no-clear', action='store_true', help='Do not clear the cards table before populating.')
    args = parser.parse_args()

    conn = create_db(args.db)
    populate_cards_table(
        conn,
        data_dir=args.data,
        creation_method=args.creation_method,
        years_to_exclude=args.exclude_years,
        clear_first=not args.no_clear
    )
    update_class_to_year_live(conn)
    conn.close()
    print("[LOG] Database initialization complete.")

if __name__ == "__main__":
    main() 