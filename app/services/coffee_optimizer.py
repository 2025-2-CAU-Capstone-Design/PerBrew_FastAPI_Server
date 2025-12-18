# coffee_tuner.py
# Modular coffee recipe tuning system based on your 27-point dataset

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator
import os

# Global variables (built once at startup)
_interpolators = None
_fine_grid = None
_ratio_levels = None

def load_and_build_model(csv_path: str = "./app/services/coffee_data.csv") -> None:
    """
    Load the dataset and build the interpolation model.
    Call this once at server startup.
    """
    global _interpolators, _fine_grid, _ratio_levels

    df = pd.read_csv(csv_path)

    # Parse TDS from "a/b" format
    def parse_tds(x):
        try:
            if pd.isna(x) or '/' not in str(x):
                return np.nan
            a, b = str(x).split('/', 1)
            return float(a.strip()) / float(b.strip())
        except:
            return np.nan

    df['tds'] = df['tds'].apply(parse_tds)

    # Manual fixes for known typos (safe to keep even if CSV is corrected)
    fixes = {13: 0.85/1.08, 18: 0.81/1.05, 19: 0.73/0.92, 21: 0.55/0.70}
    for num, val in fixes.items():
        if 'recipe_num' in df.columns:
            df.loc[df['recipe_num'] == num, 'tds'] = val

    # Grid setup
    grind_levels = np.array([75, 90, 105])
    ratio_levels = np.sort(df['ratio'].unique())  # usually [1.0, 1.6667, 3.0]
    temp_levels = np.array([85, 90, 95])

    _ratio_levels = ratio_levels

    tds_grid = np.zeros((3, 3, 3))
    taste_grid = np.zeros((3, 3, 3))

    grind_map = {75: 0, 90: 1, 105: 2}
    ratio_map = {ratio_levels[0]: 0, ratio_levels[1]: 1, ratio_levels[2]: 2}
    temp_map = {85: 0, 90: 1, 95: 2}

    for _, row in df.iterrows():
        g_idx = grind_map[row['grind_level']]
        r_idx = ratio_map[row['ratio']]
        t_idx = temp_map[row['water_temp_c']]
        tds_grid[g_idx, r_idx, t_idx] = row['tds']
        taste_grid[g_idx, r_idx, t_idx] = row['taste']

    # Build interpolators
    tds_interp = RegularGridInterpolator(
        (grind_levels, ratio_levels, temp_levels), tds_grid,
        bounds_error=False, fill_value=None
    )
    taste_interp = RegularGridInterpolator(
        (grind_levels, ratio_levels, temp_levels), taste_grid,
        bounds_error=False, fill_value=None
    )

    _interpolators = {'tds': tds_interp, 'taste': taste_interp}

    # Pre-compute fine grid for fast recommendations
    n_points = 21
    fine_grind = np.linspace(75, 105, n_points)
    fine_ratio = np.linspace(1, 3, n_points)
    fine_temp = np.linspace(85, 95, n_points)

    G, R, T = np.meshgrid(fine_grind, fine_ratio, fine_temp, indexing='ij')
    points = np.column_stack([G.ravel(), R.ravel(), T.ravel()])

    fine_tds = tds_interp(points).reshape((n_points, n_points, n_points))
    fine_taste = taste_interp(points).reshape((n_points, n_points, n_points))

    _fine_grid = {
        'grind': fine_grind,
        'ratio': fine_ratio,
        'temp': fine_temp,
        'tds': fine_tds,
        'taste': fine_taste,
        'points': points
    }

    print("Coffee tuning model loaded and ready!")


def estimate_outcome(grind: float, ratio: float, temp: float) -> dict:
    """
    Predict TDS and taste for any recipe (even outside original points).
    """
    if _interpolators is None:
        load_and_build_model()
    point = np.array([[grind, ratio, temp]])
    pred_tds = _interpolators['tds'](point)[0]
    pred_taste = _interpolators['taste'](point)[0]

    return {
        'grind_level': float(grind),
        'ratio': float(ratio),
        'water_temp_c': float(temp),
        'predicted_tds': round(pred_tds, 4),
        'predicted_taste': round(pred_taste, 2)
    }


def recommend_next_recipe(
    current_tds: float,
    current_taste: float,
    delta_tds: float = 0.0,
    delta_taste: float = 0.0,
    top_k: int = 5
) -> list[dict]:
    """
    Recommend next recipe(s) based on current result and desired improvement (deltas).
    
    Parameters:
        current_tds   : measured TDS from latest brew
        current_taste : measured taste score from latest brew
        delta_tds     : desired change in TDS (e.g., +0.01 for more extraction)
        delta_taste   : desired change in taste score (e.g., +1.0 to reduce sourness)
        top_k         : how many alternative recipes to return
    
    Returns:
        List of recommended recipes (best first)
    """
    if _fine_grid is None:
        raise RuntimeError("Model not loaded. Call load_and_build_model() first.")

    goal_tds = current_tds + delta_tds
    goal_taste = current_taste + delta_taste

    fine_tds = _fine_grid['tds']
    fine_taste = _fine_grid['taste']
    error = np.abs((fine_tds - goal_tds) * (fine_taste - goal_taste))

    best_idxs = np.argsort(error.ravel())[:top_k * 3]  # get extra to dedupe

    results = []
    seen = set()
    for idx in best_idxs:
        i, j, k = np.unravel_index(idx, error.shape)
        g = round(_fine_grid['grind'][i], 1)
        r = round(_fine_grid['ratio'][j], 3)
        t = round(_fine_grid['temp'][k], 1)
        key = (g, r, t)
        if key in seen:
            continue
        seen.add(key)

        results.append({
            'rank': len(results) + 1,
            'grind_level': g,
            'ratio': r,
            'brew_ratio_1_to': round(1 / r, 2),  # coffee:water
            'water_temp_c': t,
            'predicted_tds': round(fine_tds[i, j, k], 4),
            'predicted_taste': round(fine_taste[i, j, k], 2),
            'expected_delta_tds': round(fine_tds[i, j, k] - current_tds, 4),
            'expected_delta_taste': round(fine_taste[i, j, k] - current_taste, 2),
            'error_score': round(error[i, j, k], 6),
            'goal_tds': round(goal_tds, 4),
            'goal_taste': round(goal_taste, 2)
        })
        if len(results) >= top_k:
            break

    return results


# app/services/recipe_modifier.py

from typing import Dict, Any
from app.models.recipe import Recipe  # Your SQLAlchemy Recipe model

# Mapping from user's 1-7 feedback to desired delta
# Center is 4 = "perfect", <4 = too much of the "left" side, >4 = too much of the "right" side

FEEDBACK_MAPPING = {
    "taste": {
        # Very Acidic (1) → Very Nutty (7)
        # Low score = too acidic/sour → want to increase taste score (less sour)
        "delta_per_point": 0.35,  # each point away from 4 moves taste goal by ~0.35
        "center": 4,
    },
    "tds": {
        # Very Low (1) → Very High (7)
        # Low score = under-extracted → want higher TDS
        "delta_per_point": 0.015,  # realistic TDS adjustment per feedback point
        "center": 4,
    },
    "intensity": {
        # Weak (1) → Strong (7)
        # Low = too weak → want stronger → lower brew ratio (more coffee per water)
        # We adjust ratio: lower ratio = stronger coffee
        "ratio_delta_per_point": -0.15,  # e.g., from 1:16 to 1:14 for stronger
        "center": 4,
    },
    # "weight" slider in your UI seems to be mislabeled – based on context,
    # it's likely meant as "body/mouthfeel" or brew strength perception.
    # We'll treat it the same as intensity for simplicity.
    "weight": {
        "ratio_delta_per_point": -0.12,
        "center": 4,
    }
}


def interpret_feedback(
    taste: int,
    tds: int,
    weight: int,
    intensity: int,
) -> tuple[float, float]:
    """
    Convert 1-7 feedback scores into desired deltas for TDS and taste.
    Returns (desired_delta_tds, desired_delta_taste)
    """
    delta_tds = 0.0
    delta_taste = 0.0

    # TDS feedback
    tds_deviation = tds - FEEDBACK_MAPPING["tds"]["center"]
    delta_tds += tds_deviation * FEEDBACK_MAPPING["tds"]["delta_per_point"]

    # Taste feedback (Acidic → Nutty)
    taste_deviation = taste - FEEDBACK_MAPPING["taste"]["center"]
    delta_taste += taste_deviation * FEEDBACK_MAPPING["taste"]["delta_per_point"]

    # Intensity & Weight both affect strength → adjust ratio later in recommendation
    # We don't adjust TDS/taste directly from these

    return delta_tds, delta_taste


def modify_recipe_based_on_feedback(
    original_recipe: Recipe,
    taste: int,          # 1-7 (Acidic → Nutty)
    tds: int,            # 1-7 (Low → High)
    weight: int,         # 1-7 (perceived body/strength)
    intensity: int,      # 1-7 (Weak → Strong)
    top_k: int = 3
) -> Dict[str, Any]:
    """
    Generate a modified recipe based on user feedback.
    
    Args:
        original_recipe: SQLAlchemy Recipe object (must have grind_level, ratio, water_temp_c)
        taste, tds, weight, intensity: user ratings from 1 to 7
        top_k: how many candidates to evaluate (we return the best one)
    
    Returns:
        Dict with modified parameters ready to create a new Recipe
    """
    



    current_grind = original_recipe.grind_level
    current_ratio = 1
    if len(original_recipe.pouring_steps) > 1:
        current_ratio = original_recipe.pouring_steps[1].water_g / original_recipe.pouring_steps[2].water_g  # assuming pouring_steps[1] exists
    current_temp = original_recipe.water_temperature_c

    # First, estimate current outcome using the model
    current_pred = estimate_outcome(current_grind, current_ratio, current_temp)
    current_tds = current_pred['predicted_tds']
    current_taste = current_pred['predicted_taste']

    # Interpret feedback into desired improvements
    delta_tds, delta_taste = interpret_feedback(
        taste=taste,
        tds=tds,
        weight=weight,
        intensity=intensity,
    )

    # Get top recommendations aiming for improved TDS + taste
    candidates = recommend_next_recipe(
        current_tds=current_tds,
        current_taste=current_taste,
        delta_tds=delta_tds,
        delta_taste=delta_taste,
        top_k=top_k
    )

    if not candidates:
        raise RuntimeError("No suitable modified recipe found")

    # Pick the best candidate (rank 1)
    best = candidates[0]

    # Build modified recipe parameters
    modified_params = {
        "recipe_name": f"{original_recipe.recipe_name} (optimized)",
        "grind_level": best['grind_level'],
        "ratio": best['ratio'],  # water:coffee
        "water_temperature_c": best['water_temp_c'],
        "source": original_recipe.recipe_id,  # optional: track lineage
    }




    return modified_params