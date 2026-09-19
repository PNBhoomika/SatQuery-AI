"""
Multi-temporal sliding-window earliest-supported-date analysis engine.
Covering PS §2.2.2.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional


def find_earliest_supported_date(
    tile_stack: List[Dict[str, Any]],
    detect_pair_fn: Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]],
    min_confidence: float = 0.70,
    min_qa_coverage: float = 0.75
) -> Dict[str, Any]:
    """
    Sliding window evaluation across a sorted multi-temporal stack to identify the
    earliest supported acquisition timestamp where change first surfaced with
    monotonic consistency.

    Args:
        tile_stack: List of dicts sorted by date containing:
                    {'tile_path': str, 'date': str, 'qa_mask_path': str, 'sar_path': Optional[str]}
        detect_pair_fn: Callable taking two stack elements and returning a change_event dict.
        min_confidence: Required confidence threshold for earliest date confirmation.
        min_qa_coverage: Minimum clear-sky QA coverage requirement.

    Returns:
        dict with:
          - "earliest_supported_date": ISO8601 string or None
          - "per_date_confidence": list of {"date": str, "confidence": float, "valid": bool}
    """
    if len(tile_stack) < 2:
        return {
            "earliest_supported_date": None,
            "per_date_confidence": [],
        }

    # Sort stack chronologically by acquisition date
    sorted_stack = sorted(tile_stack, key=lambda x: x.get("date", ""))
    per_date_confidence = []
    earliest_date = None

    for i in range(len(sorted_stack) - 1):
        item_t1 = sorted_stack[i]
        item_t2 = sorted_stack[i + 1]
        t2_date = item_t2.get("date")

        result = detect_pair_fn(item_t1, item_t2)
        conf = float(result.get("confidence", 0.0))
        debug = result.get("debug", {})
        qa_cov = float(debug.get("qa_coverage", 1.0))

        is_valid = (conf >= min_confidence) and (qa_cov >= min_qa_coverage)

        per_date_confidence.append({
            "t1_date": item_t1.get("date"),
            "t2_date": t2_date,
            "confidence": conf,
            "qa_coverage": qa_cov,
            "is_valid_change": is_valid
        })

        # Monotonic rule: Lock in the first confirmed date
        if is_valid and earliest_date is None:
            earliest_date = t2_date

    return {
        "earliest_supported_date": earliest_date,
        "per_date_confidence": per_date_confidence
    }
