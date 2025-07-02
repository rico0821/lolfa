import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pandas as pd
import numpy as np
from stat_card import step1_basic_metrics, step2_team_averages, step3_individual_metrics_with_adjustment, step4_aggregate_and_apply_reliability, step5_normalize_by_position, step6_apply_weights

RAW_CSV = 'tmp/lwx_2023_raw.csv'
REPORT_CSV = 'tmp/trace_lwx_pipeline_report.csv'

# Read header from data/2023.csv
with open('data/2023.csv', 'r', encoding='utf-8') as f:
    header = f.readline().strip().split(',')

# Read Lwx rows as DataFrame
rows = []
with open(RAW_CSV, 'r', encoding='utf-8') as f:
    for line in f:
        if ':' in line:
            line = line.split(':', 2)[-1]
        row = line.strip().split(',')
        if len(row) == len(header):
            rows.append(row)

if not rows:
    print('No Lwx rows found.')
    exit(0)

df = pd.DataFrame(rows, columns=header)

# Convert columns to numeric where possible (except for known string columns)
string_cols = [
    'gameid', 'datacompleteness', 'url', 'league', 'split', 'side', 'position', 'playername', 'playerid', 'teamname', 'teamid', 'champion', 'ban1', 'ban2', 'ban3', 'ban4', 'ban5', 'pick1', 'pick2', 'pick3', 'pick4', 'pick5', 'result', 'date'
]
for col in df.columns:
    if col not in string_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

report = []
step_names = [
    'step1_basic_metrics',
    'step2_team_averages',
    'step3_individual_metrics_with_adjustment',
    'step4_aggregate_and_apply_reliability',
    'step5_normalize_by_position',
    'step6_apply_weights'
]

try:
    # Step 1
    s1 = step1_basic_metrics(df)
    nan1 = s1.isnull().any().any() or np.isinf(s1.select_dtypes(include=[np.number])).any().any()
    report.append({'step': 'step1_basic_metrics', 'has_nan_or_inf': nan1, 'shape': s1.shape})
    if nan1:
        s1.to_csv('tmp/lwx_step1_nan.csv', index=False)
        print('NaN/inf detected after step1_basic_metrics. See tmp/lwx_step1_nan.csv')
    # Step 2
    team_avgs, league_avgs = step2_team_averages(s1)
    nan2 = team_avgs.isnull().any().any() or np.isinf(team_avgs.select_dtypes(include=[np.number])).any().any()
    report.append({'step': 'step2_team_averages', 'has_nan_or_inf': nan2, 'shape': team_avgs.shape})
    if nan2:
        team_avgs.to_csv('tmp/lwx_step2_nan.csv', index=False)
        print('NaN/inf detected after step2_team_averages. See tmp/lwx_step2_nan.csv')
    # Step 3
    s3 = step3_individual_metrics_with_adjustment(s1, team_avgs, league_avgs)
    nan3 = s3.isnull().any().any() or np.isinf(s3.select_dtypes(include=[np.number])).any().any()
    report.append({'step': 'step3_individual_metrics_with_adjustment', 'has_nan_or_inf': nan3, 'shape': s3.shape})
    if nan3:
        s3.to_csv('tmp/lwx_step3_nan.csv', index=False)
        print('NaN/inf detected after step3_individual_metrics_with_adjustment. See tmp/lwx_step3_nan.csv')
    # Step 4
    s4 = step4_aggregate_and_apply_reliability(s3)
    nan4 = s4.isnull().any().any() or np.isinf(s4.select_dtypes(include=[np.number])).any().any()
    report.append({'step': 'step4_aggregate_and_apply_reliability', 'has_nan_or_inf': nan4, 'shape': s4.shape})
    if nan4:
        s4.to_csv('tmp/lwx_step4_nan.csv', index=False)
        print('NaN/inf detected after step4_aggregate_and_apply_reliability. See tmp/lwx_step4_nan.csv')
    # Step 5
    s5 = step5_normalize_by_position(s4)
    nan5 = s5.isnull().any().any() or np.isinf(s5.select_dtypes(include=[np.number])).any().any()
    report.append({'step': 'step5_normalize_by_position', 'has_nan_or_inf': nan5, 'shape': s5.shape})
    if nan5:
        s5.to_csv('tmp/lwx_step5_nan.csv', index=False)
        print('NaN/inf detected after step5_normalize_by_position. See tmp/lwx_step5_nan.csv')
    # Step 6
    s6 = step6_apply_weights(s5)
    nan6 = s6.isnull().any().any() or np.isinf(s6.select_dtypes(include=[np.number])).any().any()
    report.append({'step': 'step6_apply_weights', 'has_nan_or_inf': nan6, 'shape': s6.shape})
    if nan6:
        s6.to_csv('tmp/lwx_step6_nan.csv', index=False)
        print('NaN/inf detected after step6_apply_weights. See tmp/lwx_step6_nan.csv')
    print('Pipeline completed.')
except Exception as e:
    report.append({'step': 'exception', 'error': str(e)})
    print(f'Exception during pipeline: {e}')

pd.DataFrame(report).to_csv(REPORT_CSV, index=False)
print(f'Report saved to {REPORT_CSV}') 