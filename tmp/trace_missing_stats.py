import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from stat_card import step1_basic_metrics, step2_team_averages, step3_individual_metrics_with_adjustment, step4_aggregate_and_apply_reliability, step5_normalize_by_position, step6_apply_weights

MISSING_CSV = 'tmp/missing_stats.csv'
DATA_DIR = 'data'
REPORT_CSV = 'tmp/trace_missing_stats_report.csv'

# Helper to find the raw data file for a given year
def find_csv_for_year(year):
    for fname in os.listdir(DATA_DIR):
        if fname.endswith('.csv') and str(year) in fname:
            return os.path.join(DATA_DIR, fname)
    return None

def main():
    missing = pd.read_csv(MISSING_CSV)
    report_rows = []
    total = len(missing)
    for idx, row in missing.iterrows():
        print(f'Processing {idx+1}/{total}: {row["playername"]} ({row["teamname"]}, {row["year"]}, {row["split"]})')
        year = row['year']
        league = row['teamname'] if 'league' not in row else row['league']
        player = row['playername']
        team = row['teamname']
        split = row['split']
        # Find the raw data file
        csv_path = find_csv_for_year(year)
        if not csv_path:
            report_rows.append({**row, 'error': f'No CSV for year {year}'})
            continue
        raw_df = pd.read_csv(csv_path)
        # Try to match the player/team/split/league
        match = raw_df[(raw_df['playername'] == player) & (raw_df['teamname'] == team) & (raw_df['split'] == split)]
        if match.empty:
            report_rows.append({**row, 'error': 'No matching raw data'})
            continue
        # Run pipeline step by step
        try:
            s1 = step1_basic_metrics(match)
            if s1.isnull().any().any() or np.isinf(s1.values).any():
                report_rows.append({**row, 'error': 'NaN/inf in step1_basic_metrics'})
                continue
            team_avgs, league_avgs = step2_team_averages(s1)
            s3 = step3_individual_metrics_with_adjustment(s1, team_avgs, league_avgs)
            if s3.isnull().any().any() or np.isinf(s3.values).any():
                report_rows.append({**row, 'error': 'NaN/inf in step3_individual_metrics_with_adjustment'})
                continue
            s4 = step4_aggregate_and_apply_reliability(s3)
            if s4.isnull().any().any() or np.isinf(s4.values).any():
                report_rows.append({**row, 'error': 'NaN/inf in step4_aggregate_and_apply_reliability'})
                continue
            s5 = step5_normalize_by_position(s4)
            if s5.isnull().any().any() or np.isinf(s5.values).any():
                report_rows.append({**row, 'error': 'NaN/inf in step5_normalize_by_position'})
                continue
            s6 = step6_apply_weights(s5)
            if s6.isnull().any().any() or np.isinf(s6.values).any():
                report_rows.append({**row, 'error': 'NaN/inf in step6_apply_weights'})
                continue
            report_rows.append({**row, 'error': 'Unknown (not reproducible in pipeline)'})
        except Exception as e:
            report_rows.append({**row, 'error': f'Exception: {e}'})
        if (idx+1) % 50 == 0:
            print(f'Processed {idx+1} cards so far...')
    # Output report
    report_df = pd.DataFrame(report_rows)
    report_df.to_csv(REPORT_CSV, index=False)
    print(f'Report written to {REPORT_CSV}')

if __name__ == '__main__':
    main() 