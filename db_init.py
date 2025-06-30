import os
import sqlite3
import pandas as pd
from stat_card import (
    filter_season_data, generate_final_stat_cards
)

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

def populate_cards_table(conn, data_dir: str, creation_method: str = 'default'):
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
    insert_count = 0  # Limit to 5 splits for speed (temporary)
    for league in df['league'].dropna().unique():
        for year in df['year'].dropna().unique():
            for split in df['split'].dropna().unique():
                if insert_count >= 5:
                    print("[LOG] Reached temporary split limit (5). Stopping early.")
                    return
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
                cards['class'] = ''  # Default to empty string for now
                cards = cards[['playername', 'teamname', 'position', 'league', 'season', 'year', 'split', 'creation_method', 'class',
                               'final_offense', 'final_defense', 'final_utility', 'final_macro', 'final_clutch', 'final_consistency']]
                cards.to_sql('cards', conn, if_exists='append', index=False)
                print(f"[LOG] Inserted {len(cards)} cards for {league} {year} {split}")
                insert_count += 1

if __name__ == "__main__":
    db_path = "stat_cards.db"
    data_dir = "data"
    conn = create_db(db_path)
    populate_cards_table(conn, data_dir)
    conn.close()
    print("[LOG] Database initialization complete.") 