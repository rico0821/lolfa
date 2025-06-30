import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pandas as pd
from stat_card import step1_basic_metrics, step2_team_averages, step3_individual_metrics_with_adjustment

@pytest.fixture(scope="module")
def sample_df():
    return pd.read_csv('data/2024.csv', nrows=100)

def test_step1_basic_metrics(sample_df):
    step1 = step1_basic_metrics(sample_df)
    assert not step1.empty
    assert 'kill_participation' in step1.columns

def test_step2_team_averages(sample_df):
    step1 = step1_basic_metrics(sample_df)
    team_avgs, league_avgs = step2_team_averages(step1)
    assert not team_avgs.empty
    assert isinstance(league_avgs, dict)

def test_step3_individual_metrics_with_adjustment(sample_df):
    step1 = step1_basic_metrics(sample_df)
    team_avgs, league_avgs = step2_team_averages(step1)
    step3 = step3_individual_metrics_with_adjustment(step1, team_avgs, league_avgs)
    assert not step3.empty
    assert 'offense_dpm_adjusted' in step3.columns 

def test_generate_final_stat_cards(sample_df):
    from stat_card import generate_final_stat_cards
    # Use a small sample for speed
    cards = generate_final_stat_cards(sample_df)
    required_cols = [
        'final_offense', 'final_defense', 'final_utility',
        'final_macro', 'final_clutch', 'final_consistency',
        'playername', 'teamname'
    ]
    for col in required_cols:
        assert col in cards.columns, f"Missing column: {col}"
    # Should have at least one card
    assert not cards.empty 