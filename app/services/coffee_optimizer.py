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
    n_points = 31
    fine_grind = np.linspace(75, 105, n_points)
    fine_ratio = np.linspace(1.0, 3.0, n_points)
    fine_temp = np.linspace(85, 95, n_points)

    G, R, T = np.meshgrid(fine_grind, fine_ratio, fine_temp, indexing='ij')
    points = np.column_stack([G.ravel(), R.ravel(), T.ravel()])

    fine_tds = _interpolators['tds'](points).reshape((n_points, n_points, n_points))
    fine_taste = _interpolators['taste'](points).reshape((n_points, n_points, n_points))

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
    base_tds: float,
    base_taste: float,
    taste_fb: int,
    tds_fb: int,
    weight_fb: float = 4.0,   # 1~7
    intensity_fb: float = 4.0, # 1~7
    top_k: int = 5
) -> list[dict]:
    """
    로컬 코드 스타일의 추천: multiplicative goal 조정 + 가중치 error
    """
    if _fine_grid is None:
        raise RuntimeError("Model not loaded.")

    # 로컬 스타일 adjustment factor (지수 방식)
    def adjustment_factor(likert, intensity):
        deviation = likert - 4
        if deviation == 0:
            return 1.0
        elif deviation < 0:  # too sour/weak → increase
            return (0.94) ** (-deviation * intensity)
        else:
            return (1 / 0.9) ** (deviation * intensity)

    # intensity와 weight를 스케일링 (로컬처럼 1-7 → factor)
    intensity = intensity_fb / 4.0
    weight_taste = weight_fb / 4.0
    calc_w = weight_taste  # 로컬에서 사용된 방식

    adj_taste = adjustment_factor(taste_fb, intensity)
    adj_tds = adjustment_factor(tds_fb, intensity)

    goal_taste = base_taste * (adj_taste ** (1 / calc_w))
    goal_tds = base_tds * (adj_tds ** calc_w)

    # 클리핑
    goal_taste = np.clip(goal_taste, 1.0, 8.0)
    goal_tds = np.clip(goal_tds, 0.3, 2.0)

    # 로컬 스타일 error: 덧셈 + weight
    diff_tds = np.abs(_fine_grid['tds'] - goal_tds)
    diff_taste = np.abs(_fine_grid['taste'] - goal_taste)
    error = diff_tds + (weight_taste * diff_taste)

    best_idxs = np.argsort(error.ravel())[:top_k * 3]

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

        pred_tds = round(_fine_grid['tds'][i, j, k], 4)
        pred_taste = round(_fine_grid['taste'][i, j, k], 2)

        results.append({
            'rank': len(results) + 1,
            'grind_level': g,
            'ratio': r,
            'brew_ratio_1_to': round(1 / r, 2),
            'water_temp_c': t,
            'predicted_tds': pred_tds,
            'predicted_taste': pred_taste,
            'goal_tds': round(goal_tds, 4),
            'goal_taste': round(goal_taste, 2),
        })
        if len(results) >= top_k:
            break

    return results


# app/services/recipe_modifier.py

from typing import Dict, Any
from app.models.recipe import Recipe  # Your SQLAlchemy Recipe model

# Mapping from user's 1-7 feedback to desired delta
# Center is 4 = "perfect", <4 = too much of the "left" side, >4 = too much of the "right" side
"""
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
"""

"""
def interpret_feedback(
    taste: int,
    tds: int,
    weight: int,
    intensity: int,
) -> tuple[float, float]:
    
    #Convert 1-7 feedback scores into desired deltas for TDS and taste.
    #Returns (desired_delta_tds, desired_delta_taste)
    
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
"""

def modify_recipe_based_on_feedback(
    original_recipe: Recipe,
    taste: int,          # 1-7 Acidic → Nutty
    tds: int,            # 1-7 Low → High
    weight: int = 4,     # 1-7 (body perception)
    intensity: int = 4,  # 1-7 Weak → Strong
    top_k: int = 5
) -> Dict[str, Any]:
    """
    로컬 스타일로 완전히 통합된 수정 함수
    """
    # 현재 ratio 추출 (pouring_steps 기반 - 실제 앱에 맞게)
    current_grind = original_recipe.grind_level
    current_temp = original_recipe.water_temperature_c

    # ratio: pouring_steps에서 추출하거나 기본값
    current_ratio = 1.6667  # 기본값
    if hasattr(original_recipe, 'pouring_steps') and len(original_recipe.pouring_steps) > 2:
        # 예: pour2 / pour3 물 양 비율 등 - 실제 로직에 맞게 조정
        try:
            current_ratio = original_recipe.pouring_steps[1].water_g / original_recipe.pouring_steps[2].water_g
        except:
            pass

    # 현재 예측
    current_pred = estimate_outcome(current_grind, current_ratio, current_temp)
    base_tds = current_pred['predicted_tds']
    base_taste = current_pred['predicted_taste']

    # 로컬 스타일 추천
    candidates = recommend_next_recipe(
        base_tds=base_tds,
        base_taste=base_taste,
        taste_fb=taste,
        tds_fb=tds,
        weight_fb=weight,
        intensity_fb=intensity,
        top_k=top_k
    )

    if not candidates:
        raise RuntimeError("No recommendation found")

    best = candidates[0]

    # 로컬처럼 강도 피드백으로 ratio 미세 조정
    strength_deviation = (intensity + weight) / 2 - 4
    pour_adjust = strength_deviation * -0.08  # 강하면 ratio 낮춤 (더 진하게)
    adjusted_ratio = max(1.0, min(3.0, best['ratio'] + pour_adjust))

    modified_params = {
        "recipe_name": f"{original_recipe.recipe_name} (optimized v2)",
        "grind_level": best['grind_level'],
        "ratio": adjusted_ratio,
        "water_temperature_c": best['water_temp_c'],
        "source": original_recipe.recipe_id,
        # 추가 정보 (디버깅용)
        "predicted_tds": best['predicted_tds'],
        "predicted_taste": best['predicted_taste'],
        "goal_tds": best['goal_tds'],
        "goal_taste": best['goal_taste']
    }

    return modified_params