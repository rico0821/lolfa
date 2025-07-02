import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = 'stat_cards.db'
STAT_COLS = [
    'final_offense', 'final_defense', 'final_utility',
    'final_macro', 'final_clutch', 'final_consistency'
]

OUTPUT_CSV = 'tmp/missing_stats.csv'

def main():
    conn = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT id, playername, teamname, year, split, {', '.join(STAT_COLS)}
        FROM cards
    """
    df = pd.read_sql_query(query, conn)
    # Find rows with any stat column as NaN, inf, or -inf
    mask = df[STAT_COLS].isnull().any(axis=1) | np.isinf(df[STAT_COLS]).any(axis=1)
    missing = df[mask]
    if missing.empty:
        print('No cards with missing or non-finite stat values.')
    else:
        print(f'Found {len(missing)} cards with missing or non-finite stat values.')
        print(f'Exporting to {OUTPUT_CSV}')
        missing.to_csv(OUTPUT_CSV, index=False)

def export_partial_league_splits():
    years = range(2014, 2026)
    results = []
    outdir = 'tmp'
    os.makedirs(outdir, exist_ok=True)
    for y in years:
        f = f'data/{y}.csv'
        if os.path.exists(f):
            df = pd.read_csv(f)
            partial = df[df['datacompleteness'] == 'partial']
            if not partial.empty:
                for _, row in partial[['league', 'split']].drop_duplicates().iterrows():
                    results.append({'year': y, 'league': row['league'], 'split': row['split']})
    pd.DataFrame(results).to_csv(f'{outdir}/partial_league_splits_2014_2025.csv', index=False)

def export_always_filled_player_columns():
    years = range(2014, 2026)
    outdir = 'tmp'
    os.makedirs(outdir, exist_ok=True)
    summary = []
    for y in years:
        f = f'data/{y}.csv'
        if os.path.exists(f):
            df = pd.read_csv(f)
            player_rows = df[df['position'] != 'team']
            always_filled = [col for col in player_rows.columns if not player_rows[col].isnull().any()]
            for col in always_filled:
                summary.append({'year': y, 'column': col})
    pd.DataFrame(summary).to_csv(f'{outdir}/always_filled_player_columns_2014_2025.csv', index=False)

def print_partial_data_proportion():
    years = range(2014, 2026)
    total_rows = 0
    partial_rows = 0
    for y in years:
        f = f'data/{y}.csv'
        if os.path.exists(f):
            df = pd.read_csv(f)
            player_rows = df[df['position'] != 'team']
            total_rows += len(player_rows)
            partial_rows += (player_rows['datacompleteness'] == 'partial').sum()
    print(f'Total player rows: {total_rows}')
    print(f'Partial player rows: {partial_rows}')
    if total_rows > 0:
        print(f'Proportion partial: {partial_rows/total_rows:.4f}')
    else:
        print('No player rows found.')

def export_partial_data_by_league():
    years = range(2014, 2026)
    league_stats = {}
    for y in years:
        f = f'data/{y}.csv'
        if os.path.exists(f):
            df = pd.read_csv(f)
            player_rows = df[df['position'] != 'team']
            for league, group in player_rows.groupby('league'):
                total = len(group)
                partial = (group['datacompleteness'] == 'partial').sum()
                if league not in league_stats:
                    league_stats[league] = {'total': 0, 'partial': 0}
                league_stats[league]['total'] += total
                league_stats[league]['partial'] += partial
    out = []
    for league, stats in league_stats.items():
        proportion = stats['partial'] / stats['total'] if stats['total'] > 0 else 0
        out.append({'league': league, 'total': stats['total'], 'partial': stats['partial'], 'proportion_partial': proportion})
    pd.DataFrame(out).to_csv('tmp/partial_data_by_league.csv', index=False)
    print('Exported league breakdown to tmp/partial_data_by_league.csv')

if __name__ == '__main__':
    main()
    # Additional: print NaN columns for first 5 unique players
    df = pd.read_csv(OUTPUT_CSV)
    players = df['playername'].unique()[:5]
    for p in players:
        sub = df[df['playername'] == p]
        nan_cols = sub.columns[sub.isnull().any()].tolist()
        print(f'Player: {p} | Columns with NaN: {nan_cols}')
    # Additional: print NaN columns in raw data for 5 error players
    raw_df = pd.read_csv('data/2017.csv')
    error_players = ['Amazing','Cinkrof','CozQ','Dreams','HeaQ']
    for p in error_players:
        sub = raw_df[raw_df['playername'] == p]
        nan_cols = sub.columns[sub.isnull().any()].tolist()
        print(f'[RAW] Player: {p} | Columns with NaN: {nan_cols}')
    # Additional: check null rate for ban5, pick1-5 in 2017.csv
    cols_to_check = ['ban5', 'pick1', 'pick2', 'pick3', 'pick4', 'pick5']
    print('\n[NULL RATE in 2017.csv]')
    for col in cols_to_check:
        if col in raw_df.columns:
            null_rate = raw_df[col].isnull().mean() * 100
            print(f'{col}: {null_rate:.1f}% null')
        else:
            print(f'{col}: not found in columns')
    export_partial_league_splits()
    export_always_filled_player_columns()
    print_partial_data_proportion()
    export_partial_data_by_league() 