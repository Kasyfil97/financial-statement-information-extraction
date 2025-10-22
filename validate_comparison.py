"""
A script to compare and analyze numerical values between two JSON files, typically comparing baseline data with GPT-generated results.

This script provides functionality to:
1. Load and parse JSON files
2. Extract numerical values (current_year and previous_year) from nested JSON structures
3. Compute various comparison metrics (Accuracy, MAE, MAPE, RMSE, R²)
4. Generate detailed comparison summaries

Key Features:
- Handles nested JSON structures and arrays
- Computes common statistical metrics for numerical comparisons
- Identifies missing fields between files
- Generates summary statistics and detailed reports
- Saves comparison results to a JSON file

Metrics Computed:
- Accuracy (%): Percentage of exact matches
- MAE (Mean Absolute Error): Average absolute difference between values
- MAPE (%): Mean Absolute Percentage Error
- RMSE: Root Mean Square Error
- R²: Coefficient of determination

Usage:
    python validate_comparison.py

Input Files:
    - report.json: The baseline/ground truth file
    - report_baseline_gpt.json: The file to compare against (typically GPT-generated)

Output:
    - Prints comparison summary to console
    - Saves detailed results to 'comparison_result.json'
"""

import json
from pathlib import Path
from typing import Dict, Any
import math
import numpy as np

'''

'''

def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_amounts(data: Dict[str, Any], prefix: str = "") -> Dict[str, float]:
    """Ambil hanya nilai numerik dari current_year / previous_year"""
    result = {}
    if isinstance(data, dict):
        for k, v in data.items():
            key_path = f"{prefix}.{k}" if prefix else k
            if k in ("current_year", "previous_year") and isinstance(v, (int, float)):
                result[key_path] = v
            elif isinstance(v, dict):
                result.update(extract_amounts(v, key_path))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    result.update(extract_amounts(item, f"{key_path}[{i}]"))
    return result


def compute_metrics(base: Dict[str, float], target: Dict[str, float]) -> Dict[str, float]:
    common_keys = sorted(set(base.keys()) & set(target.keys()))
    if not common_keys:
        return {}

    y_true = np.array([base[k] for k in common_keys])
    y_pred = np.array([target[k] for k in common_keys])

    diff = y_pred - y_true
    abs_diff = np.abs(diff)
    abs_pct_diff = np.abs(diff / np.where(y_true != 0, y_true, np.nan)) * 100

    mae = np.nanmean(abs_diff)
    mape = np.nanmean(abs_pct_diff)
    rmse = math.sqrt(np.nanmean(diff ** 2))
    r2 = 1 - np.nanmean((diff) ** 2) / np.nanmean((y_true - np.nanmean(y_true)) ** 2)

    accuracy = (np.sum(abs_diff == 0) / len(common_keys)) * 100

    return {
        "Accuracy (%)": round(accuracy, 2),
        "MAE": round(mae, 2),
        "MAPE (%)": round(mape, 2),
        "RMSE": round(rmse, 2),
        "R²": round(r2, 4)
    }


def compare_and_score(your_file: str, my_file: str):
    yours = load_json(your_file)
    mine = load_json(my_file)

    base = extract_amounts(yours)
    target = extract_amounts(mine)

    missing_in_target = sorted(set(base.keys()) - set(target.keys()))
    missing_in_base = sorted(set(target.keys()) - set(base.keys()))

    metrics = compute_metrics(base, target)

    result = {
        "summary": {
            "total_fields_mine": len(base),
            "total_fields_gpt": len(target),
            "common_fields": len(set(base.keys()) & set(target.keys())),
            "missing_in_mine": len(missing_in_base),
            "missing_in_gpt": len(missing_in_target),
            "missing_rate (%)": round(((len(missing_in_target) + len(missing_in_base)) / (len(base) + len(target)) * 100), 2)
        },
        "metrics": metrics,
        "missing_in_mine": missing_in_base,
        "missing_in_gpt": missing_in_target
    }

    print("\n=== NUMERIC COMPARISON SUMMARY ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    with open("validation_comparison_report.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print("\n📁 comparison_metrics_result.json saved.")


if __name__ == "__main__":
    compare_and_score("report.json", "report_baseline_gpt.json")
