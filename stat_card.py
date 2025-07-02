import pandas as pd
import numpy as np
from typing import Tuple, Dict

def step1_basic_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate basic per-game metrics for each player row.

    Args:
        df: Raw DataFrame of player-game stats.
    Returns:
        DataFrame with additional calculated metrics.
    """
    df = df.copy()
    df['game_length_minutes'] = df['gamelength'] / 60
    df['kill_participation'] = (df['kills'] + df['assists']) / df['teamkills']
    df['damage_per_gold'] = df['damagetochampions'] / df['earnedgold']
    df['deaths_per_minute'] = df['deaths'] / df['game_length_minutes']
    df['kda_ratio'] = (df['kills'] + df['assists']) / np.maximum(df['deaths'], 1)
    df['ward_score'] = df['wpm'] + df['wcpm']
    df['assist_to_kill_ratio'] = df['assists'] / np.maximum(df['kills'], 1)
    df['total_team_objectives'] = (
        df['dragons'] + df['barons'] + df['heralds'] + df['towers'] + df['void_grubs'] + df['atakhans']
    )
    df['total_all_objectives'] = (
        df['dragons'] + df['opp_dragons'] +
        df['barons'] + df['opp_barons'] +
        df['heralds'] + df['opp_heralds'] +
        df['towers'] + df['opp_towers'] +
        df['void_grubs'] + df['opp_void_grubs'] +
        df['atakhans'] + df['opp_atakhans']
    )
    df['objective_participation'] = (df['total_team_objectives'] / np.maximum(df['total_all_objectives'], 1)) * 100
    df['multikill_score'] = df['doublekills'] + df['triplekills'] + df['quadrakills'] + df['pentakills']
    result_columns = [
        'playername', 'teamname', 'position', 'champion', 'result', 'game_length_minutes',
        'dpm', 'damageshare', 'vspm', 'turretplates', 'assists', 'firstbloodassist',
        'kill_participation', 'damage_per_gold', 'deaths_per_minute', 'kda_ratio',
        'damagetakenperminute', 'ward_score', 'assist_to_kill_ratio',
        'objective_participation', 'multikill_score'
    ]
    return df[result_columns].copy()

def step2_team_averages(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Compute team and league averages for adjustment.

    Args:
        df: DataFrame from step1_basic_metrics.
    Returns:
        (team_averages DataFrame, league_avg_dict)
    """
    team_adjustment_stats = [
        'dpm', 'deaths_per_minute', 'ward_score', 'objective_participation', 'vspm'
    ]
    team_averages = df.groupby('teamname')[team_adjustment_stats].mean().reset_index()
    team_averages.columns = ['teamname'] + [f'team_avg_{col}' for col in team_adjustment_stats]
    league_averages = df[team_adjustment_stats].mean()
    league_avg_dict = {f'league_avg_{col}': league_averages[col] for col in team_adjustment_stats}
    for stat in team_adjustment_stats:
        team_averages[f'team_index_{stat}'] = (
            team_averages[f'team_avg_{stat}'] / league_averages[stat]
        )
    return team_averages, league_avg_dict

def step3_individual_metrics_with_adjustment(
    df: pd.DataFrame,
    team_averages: pd.DataFrame,
    league_averages: Dict[str, float]
) -> pd.DataFrame:
    """Apply team/league adjustment and compute final per-game metrics.

    Args:
        df: DataFrame from step1_basic_metrics.
        team_averages: Output from step2_team_averages.
        league_averages: Output from step2_team_averages.
    Returns:
        DataFrame with adjusted metrics for each player-game.
    """
    result_df = df.copy()
    result_df = result_df.merge(team_averages, on='teamname', how='left')
    result_df['offense_dpm_adjusted'] = result_df['dpm'] / result_df['team_index_dpm']
    result_df['offense_kill_participation'] = result_df['kill_participation']
    result_df['offense_damage_per_gold'] = result_df['damage_per_gold']
    result_df['offense_damage_share'] = result_df['damageshare']
    result_df['defense_deaths_per_min_adjusted'] = result_df['deaths_per_minute'] * result_df['team_index_deaths_per_minute']
    result_df['defense_damage_taken'] = result_df['damagetakenperminute']
    result_df['defense_kda'] = result_df['kda_ratio']
    result_df['utility_ward_score_adjusted'] = result_df['ward_score'] / result_df['team_index_ward_score']
    result_df['utility_assists'] = result_df['assists']
    result_df['utility_assist_ratio'] = result_df['assist_to_kill_ratio']
    result_df['utility_fb_assist'] = result_df['firstbloodassist']
    result_df['macro_objective_participation_adjusted'] = result_df['objective_participation'] / result_df['team_index_objective_participation']
    result_df['macro_turret_plates'] = result_df['turretplates']
    result_df['macro_vision_score_adjusted'] = result_df['vspm'] / result_df['team_index_vspm']
    final_columns = [
        'playername', 'teamname', 'position', 'champion', 'result', 'game_length_minutes',
        'offense_dpm_adjusted', 'offense_kill_participation', 'offense_damage_per_gold', 'offense_damage_share',
        'defense_deaths_per_min_adjusted', 'defense_damage_taken', 'defense_kda',
        'utility_ward_score_adjusted', 'utility_assists', 'utility_assist_ratio', 'utility_fb_assist',
        'macro_objective_participation_adjusted', 'macro_turret_plates', 'macro_vision_score_adjusted',
        'multikill_score'
    ]
    return result_df[final_columns].copy()

def filter_season_data(
    df: pd.DataFrame,
    league: str,
    year: int,
    split: str,
    playoffs: int = 0
) -> pd.DataFrame:
    """Filter for a specific league, year, split, regular season, and player rows.

    Args:
        df: Raw DataFrame.
        league: League name (e.g., 'LCK').
        year: Year (e.g., 2024).
        split: Split name (e.g., 'Spring').
        playoffs: 0 for regular season, 1 for playoffs.
    Returns:
        Filtered DataFrame.
    """
    return df[(df['league'] == league) &
              (df['year'] == year) &
              (df['split'] == split) &
              (df['playoffs'] == playoffs) &
              (df['position'] != 'team') &
              (df['playername'].notna()) &
              (df['playername'] != '')].copy()

def aggregate_player_cards(
    df: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate per-player-season stats for card output.

    Args:
        df: DataFrame after stat processing (should include final stats columns).
    Returns:
        DataFrame with one row per player, including meta info and 6 final stats.
    """
    # Meta info
    meta_cols = ['playername', 'teamname', 'league', 'year', 'split']
    stat_cols = [
        'final_offense', 'final_defense', 'final_utility',
        'final_macro', 'final_clutch', 'final_consistency'
    ]
    # Use the last row for team/league/season info (should be the same for all rows per player)
    agg = df.groupby('playername').agg({
        'teamname': 'last',
        'league': 'last',
        'year': 'last',
        'split': 'last',
        **{col: 'mean' for col in stat_cols}
    }).reset_index()
    # Add season string
    agg['season'] = agg['year'].astype(str) + ' ' + agg['split']
    # Reorder columns
    out_cols = ['playername', 'teamname', 'league', 'season'] + stat_cols
    return agg[out_cols].copy()

def step4_aggregate_and_apply_reliability(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-player stats and apply reliability coefficient."""
    player_aggregated = df.groupby(['playername', 'teamname', 'position']).agg({
        'offense_dpm_adjusted': 'mean',
        'offense_kill_participation': 'mean',
        'offense_damage_per_gold': 'mean',
        'offense_damage_share': 'mean',
        'defense_deaths_per_min_adjusted': 'mean',
        'defense_damage_taken': 'mean',
        'defense_kda': 'mean',
        'utility_ward_score_adjusted': 'mean',
        'utility_assists': 'mean',
        'utility_assist_ratio': 'mean',
        'utility_fb_assist': 'mean',
        'macro_objective_participation_adjusted': 'mean',
        'macro_turret_plates': 'mean',
        'macro_vision_score_adjusted': 'mean',
        'multikill_score': 'mean'
    }).reset_index()
    # Reliability calculation
    player_reliability = []
    for player in df['playername'].unique():
        player_data = df[df['playername'] == player]
        games_played = len(player_data)
        avg_games = df.groupby('playername').size().mean()
        confidence_games = min(games_played / avg_games, 1.0)
        dpm_values = player_data['offense_dpm_adjusted'].values
        kda_values = player_data['defense_kda'].values
        dpm_mad = np.mean(np.abs(dpm_values - dpm_values.mean())) if len(dpm_values) > 1 else 0
        kda_mad = np.mean(np.abs(kda_values - kda_values.mean())) if len(kda_values) > 1 else 0
        avg_deviation = (dpm_mad + kda_mad) / 2
        player_reliability.append({
            'playername': player,
            'games_played': games_played,
            'confidence_games': confidence_games,
            'avg_deviation': avg_deviation
        })
    reliability_df = pd.DataFrame(player_reliability)
    min_dev = reliability_df['avg_deviation'].min()
    max_dev = reliability_df['avg_deviation'].max()
    if max_dev > min_dev:
        reliability_df['performance_variance'] = 1 - (reliability_df['avg_deviation'] - min_dev) / (max_dev - min_dev)
    else:
        reliability_df['performance_variance'] = 1.0
    reliability_df['final_reliability'] = reliability_df['confidence_games'] * reliability_df['performance_variance']
    result_df = player_aggregated.merge(reliability_df[['playername', 'final_reliability', 'games_played']], on='playername', how='left')
    # Apply reliability to metrics
    reliability_metrics = [
        'offense_dpm_adjusted', 'offense_kill_participation', 'offense_damage_per_gold', 'offense_damage_share',
        'defense_deaths_per_min_adjusted', 'defense_damage_taken', 'defense_kda',
        'utility_ward_score_adjusted', 'utility_assists', 'utility_assist_ratio', 'utility_fb_assist',
        'macro_objective_participation_adjusted', 'macro_turret_plates', 'macro_vision_score_adjusted',
        'multikill_score'
    ]
    for metric in reliability_metrics:
        result_df[f'{metric}_reliable'] = result_df[metric] * result_df['final_reliability']
    return result_df

def step5_normalize_by_position(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize reliable metrics by position (min-max 50-100)."""
    result_df = df.copy()
    positive_metrics = [
        'offense_dpm_adjusted_reliable', 'offense_kill_participation_reliable', 'offense_damage_per_gold_reliable', 'offense_damage_share_reliable',
        'defense_damage_taken_reliable', 'defense_kda_reliable',
        'utility_ward_score_adjusted_reliable', 'utility_assists_reliable', 'utility_assist_ratio_reliable', 'utility_fb_assist_reliable',
        'macro_objective_participation_adjusted_reliable', 'macro_turret_plates_reliable', 'macro_vision_score_adjusted_reliable',
        'multikill_score_reliable'
    ]
    negative_metrics = [
        'defense_deaths_per_min_adjusted_reliable'
    ]
    for position in result_df['position'].unique():
        pos_mask = result_df['position'] == position
        pos_data = result_df[pos_mask]
        # Positive metrics
        for metric in positive_metrics:
            min_val = pos_data[metric].min()
            max_val = pos_data[metric].max()
            if max_val > min_val:
                result_df.loc[pos_mask, f'{metric}_normalized'] = 50 + (pos_data[metric] - min_val) / (max_val - min_val) * 50
            else:
                # If all values are the same (including all zero), set to 75.0
                result_df.loc[pos_mask, f'{metric}_normalized'] = 75.0
        # Negative metrics (lower is better)
        for metric in negative_metrics:
            min_val = pos_data[metric].min()
            max_val = pos_data[metric].max()
            if max_val > min_val:
                result_df.loc[pos_mask, f'{metric}_normalized'] = 50 + (1 - (pos_data[metric] - min_val) / (max_val - min_val)) * 50
            else:
                result_df.loc[pos_mask, f'{metric}_normalized'] = 75.0
    return result_df

def step6_apply_weights(df: pd.DataFrame) -> pd.DataFrame:
    """Apply weights to normalized metrics to produce final stat columns."""
    result_df = df.copy()
    # Offense
    result_df['final_offense'] = (
        result_df['offense_dpm_adjusted_reliable_normalized'] * 0.35 +
        result_df['offense_kill_participation_reliable_normalized'] * 0.25 +
        result_df['offense_damage_per_gold_reliable_normalized'] * 0.20 +
        result_df['offense_damage_share_reliable_normalized'] * 0.20
    )
    # Defense
    result_df['final_defense'] = (
        result_df['defense_deaths_per_min_adjusted_reliable_normalized'] * 0.40 +
        result_df['defense_damage_taken_reliable_normalized'] * 0.30 +
        result_df['defense_kda_reliable_normalized'] * 0.30
    )
    # Utility
    result_df['final_utility'] = (
        result_df['utility_ward_score_adjusted_reliable_normalized'] * 0.20 +
        result_df['utility_assists_reliable_normalized'] * 0.35 +
        result_df['utility_assist_ratio_reliable_normalized'] * 0.25 +
        result_df['utility_fb_assist_reliable_normalized'] * 0.20
    )
    # Macro
    result_df['final_macro'] = (
        result_df['macro_objective_participation_adjusted_reliable_normalized'] * 0.50 +
        result_df['macro_turret_plates_reliable_normalized'] * 0.30 +
        result_df['macro_vision_score_adjusted_reliable_normalized'] * 0.20
    )
    # Clutch
    result_df['final_clutch'] = result_df['multikill_score_reliable_normalized']
    # Consistency (normalized reliability)
    for position in result_df['position'].unique():
        pos_mask = result_df['position'] == position
        pos_data = result_df[pos_mask]
        min_val = pos_data['final_reliability'].min()
        max_val = pos_data['final_reliability'].max()
        if max_val > min_val:
            result_df.loc[pos_mask, 'final_consistency'] = 50 + (pos_data['final_reliability'] - min_val) / (max_val - min_val) * 50
        else:
            result_df.loc[pos_mask, 'final_consistency'] = 75.0
    return result_df

def generate_final_stat_cards(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full stat card pipeline and return a DataFrame with all final_* columns."""
    step1 = step1_basic_metrics(df)
    team_avgs, league_avgs = step2_team_averages(step1)
    step3 = step3_individual_metrics_with_adjustment(step1, team_avgs, league_avgs)
    step4 = step4_aggregate_and_apply_reliability(step3)
    step5 = step5_normalize_by_position(step4)
    final = step6_apply_weights(step5)
    return final 