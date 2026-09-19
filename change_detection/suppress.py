"""
Multi-stage false-alarm suppression pipeline for satellite change detection.
Covering PS §2.2.3 (Precision > Recall bias).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import numpy as np


class FalseAlarmSuppressor:
    """
    Fixed-order 5-stage false-alarm suppression pipeline:
      Stage 1: Optical QA Masking (zero out clouds, shadows, snow, haze, saturation)
      Stage 2: Registration Validation & Offset Tracking
      Stage 3: Seasonal Baseline & Radiometric Normalization
      Stage 4: Sentinel-1 SAR Backscatter Fusion (VV/VH confirmation)
      Stage 5: Calibrated Confidence Weighting
    """

    def __init__(
        self,
        sar_agreement_threshold: float = 0.20,
        view_angle_max_delta: float = 15.0,
        seasonal_sigma_threshold: float = 2.0,
        weights: Optional[Dict[str, float]] = None
    ):
        self.sar_agreement_threshold = sar_agreement_threshold
        self.view_angle_max_delta = view_angle_max_delta
        self.seasonal_sigma_threshold = seasonal_sigma_threshold
        self.weights = weights or {
            "w_model": 0.40,
            "w_qa": 0.20,
            "w_sar": 0.15,
            "w_seasonal": 0.15,
            "w_reg": 0.10,
        }

    def suppress(
        self,
        raw_change_prob: np.ndarray,
        qa_decoded_t1: Dict[str, np.ndarray],
        qa_decoded_t2: Dict[str, np.ndarray],
        registration_offset: Tuple[float, float],
        registration_conf: float,
        seasonal_delta: float,
        sar_t1: Optional[np.ndarray] = None,
        sar_t2: Optional[np.ndarray] = None,
        view_angle_consistent: bool = True
    ) -> Tuple[np.ndarray, float, List[str], Dict[str, Optional[float]]]:
        """
        Execute full suppression pipeline.

        Returns:
            tuple (suppressed_mask, final_confidence, stages_fired, debug_metrics)
        """
        stages_fired = []
        h, w = raw_change_prob.shape[-2], raw_change_prob.shape[-1]
        prob = raw_change_prob.copy().reshape((h, w))

        # -------------------------------------------------------------
        # Stage 1: Optical QA Masking
        # -------------------------------------------------------------
        usable_t1 = qa_decoded_t1.get("usable", np.ones((h, w), dtype=bool))
        usable_t2 = qa_decoded_t2.get("usable", np.ones((h, w), dtype=bool))
        joint_usable = usable_t1 & usable_t2
        qa_coverage = float(np.mean(joint_usable))

        # Zero out un-usable pixels (clouds, cloud shadows, snow, saturated)
        prob[~joint_usable] = 0.0
        stages_fired.append("qa")

        # -------------------------------------------------------------
        # Stage 2: Registration Validation
        # -------------------------------------------------------------
        dx, dy = registration_offset
        offset_mag = float(np.hypot(dx, dy))
        if offset_mag > 2.5:
            # Registration offset too severe to be reliable without ground control
            prob *= 0.5
        stages_fired.append("registration")

        # -------------------------------------------------------------
        # Stage 3: Seasonal Phenology & View Angle Check
        # -------------------------------------------------------------
        # If view angle is severely mismatched (>15 deg) and SAR is absent, heavily penalize
        if not view_angle_consistent and (sar_t1 is None or sar_t2 is None):
            prob *= 0.2
        # If seasonal delta is within normal phenological variation, suppress
        if abs(seasonal_delta) < 0.05:
            prob *= 0.8
        stages_fired.append("seasonal")

        # -------------------------------------------------------------
        # Stage 4: SAR Fusion (Sentinel-1 VV/VH backscatter verification)
        # -------------------------------------------------------------
        sar_agreement: Optional[float] = None
        sar_fused = False
        if sar_t1 is not None and sar_t2 is not None:
            sar_fused = True
            stages_fired.append("sar")
            # Compute SAR backscatter magnitude delta
            sar_delta = np.mean(np.abs(sar_t2.astype(np.float32) - sar_t1.astype(np.float32)))
            sar_agreement = float(np.clip(sar_delta / (self.sar_agreement_threshold + 1e-6), 0.0, 1.0))
            if sar_agreement < 0.2:
                # Structural backscatter does not support optical change -> dampen
                prob *= 0.6
        else:
            # Missing SAR: slightly penalize confidence to reflect unverified radar status
            prob *= 0.9

        # -------------------------------------------------------------
        # Stage 5: Calibrated Confidence Weighting
        # -------------------------------------------------------------
        stages_fired.append("confidence")
        mean_model_prob = float(np.mean(prob[joint_usable])) if np.any(joint_usable) else 0.0
        sar_weight_term = sar_agreement if sar_agreement is not None else 0.5

        final_confidence = (
            self.weights["w_model"] * mean_model_prob
            + self.weights["w_qa"] * qa_coverage
            + self.weights["w_sar"] * sar_weight_term
            + self.weights["w_seasonal"] * max(0.0, 1.0 - abs(seasonal_delta))
            + self.weights["w_reg"] * registration_conf
        )
        final_confidence = float(np.clip(final_confidence, 0.0, 1.0))

        # Precision-biased binarization threshold (default 0.55)
        binary_mask = (prob > 0.55).astype(np.uint8)

        debug_metrics = {
            "raw_change_prob": float(np.mean(raw_change_prob)),
            "qa_coverage": qa_coverage,
            "sar_agreement": sar_agreement,
            "seasonal_delta": float(seasonal_delta),
            "registration_confidence": float(registration_conf),
        }

        return binary_mask, final_confidence, stages_fired, debug_metrics
