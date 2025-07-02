import os
import pandas as pd
import numpy as np
from stat_card import step1_basic_metrics, step2_team_averages, step3_individual_metrics_with_adjustment, step4_aggregate_and_apply_reliability, step5_normalize_by_position, step6_apply_weights

data_path = 'data/2022.csv'
outdir = 'tmp'
os.makedirs(outdir, exist_ok=True)

# 1. Load raw data
raw = pd.read_csv(data_path)
# 2. Filter for Faker, T1, LCK, 2022, Spring
mask = (
    raw['playername'].str.contains('Faker', na=False) &
    raw['teamname'].str.contains('T1', na=False) &
    (raw['league'] == 'LCK') &
    (raw['year'] == 2022) &
    (raw['split'].astype(str).str.strip().str.lower() == 'spring')
)
faker_rows = raw[mask].copy()
faker_rows.to_csv(f'{outdir}/faker_2022_spring_raw.csv', index=False)
print(f'Raw Faker 2022 Spring rows: {len(faker_rows)}')
if faker_rows.empty:
    print('No rows found for Faker 2022 Spring.')
    exit(0)

# 3. Filter out partials
non_partial = faker_rows[faker_rows['datacompleteness'] != 'partial'].copy()
non_partial.to_csv(f'{outdir}/faker_2022_spring_nonpartial.csv', index=False)
print(f'Non-partial rows: {len(non_partial)}')
if non_partial.empty:
    print('All rows are partial. Stopping.')
    exit(0)

# 4. Stat pipeline step-by-step
try:
    s1 = step1_basic_metrics(non_partial)
    s1.to_csv(f'{outdir}/faker_2022_spring_step1.csv', index=False)
    if s1.isnull().any().any() or np.isinf(s1.values).any():
        print('NaN/inf in step1_basic_metrics')
        print(s1.isnull().sum())
        print(np.isinf(s1.values).sum())
        exit(0)
    team_avgs, league_avgs = step2_team_averages(s1)
    s3 = step3_individual_metrics_with_adjustment(s1, team_avgs, league_avgs)
    s3.to_csv(f'{outdir}/faker_2022_spring_step3.csv', index=False)
    if s3.isnull().any().any() or np.isinf(s3.values).any():
        print('NaN/inf in step3_individual_metrics_with_adjustment')
        print(s3.isnull().sum())
        print(np.isinf(s3.values).sum())
        exit(0)
    s4 = step4_aggregate_and_apply_reliability(s3)
    s4.to_csv(f'{outdir}/faker_2022_spring_step4.csv', index=False)
    if s4.isnull().any().any() or np.isinf(s4.values).any():
        print('NaN/inf in step4_aggregate_and_apply_reliability')
        print(s4.isnull().sum())
        print(np.isinf(s4.values).sum())
        exit(0)
    s5 = step5_normalize_by_position(s4)
    s5.to_csv(f'{outdir}/faker_2022_spring_step5.csv', index=False)
    if s5.isnull().any().any() or np.isinf(s5.values).any():
        print('NaN/inf in step5_normalize_by_position')
        print(s5.isnull().sum())
        print(np.isinf(s5.values).sum())
        exit(0)
    s6 = step6_apply_weights(s5)
    s6.to_csv(f'{outdir}/faker_2022_spring_step6.csv', index=False)
    if s6.isnull().any().any() or np.isinf(s6.values).any():
        print('NaN/inf in step6_apply_weights')
        print(s6.isnull().sum())
        print(np.isinf(s6.values).sum())
        exit(0)
    print('Faker 2022 Spring successfully processed through the pipeline.')
    print(s6)
except Exception as e:
    print(f'Exception in pipeline: {e}') 