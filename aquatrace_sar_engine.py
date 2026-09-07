"""
aquatrace_sar_engine.py
Production Inference & Preprocessing Pipeline for AquaTrace SAR Segmentation
"""

import time
from typing import Dict, Any, Union
import numpy as np
from PIL import Image
import tensorflow as tf


class SARSpillDetector:
    def __init__(self, model_path: str = "deeplab_final_model.h5"):
        self.model = tf.keras.models.load_model(model_path, compile=False)
        self._warmup()

    def _warmup(self):
        dummy_tensor = np.zeros((1, 256, 256, 3), dtype=np.float32)
        _ = self.model.predict(dummy_tensor, verbose=0)

    def preprocess(self, input_source: Union[str, Image.Image, np.ndarray]) -> np.ndarray:
        if isinstance(input_source, str):
            img = Image.open(input_source)
        elif isinstance(input_source, np.ndarray):
            img = Image.fromarray(input_source)
        else:
            img = input_source

        img_rgb = img.convert("RGB").resize((256, 256), Image.BILINEAR)
        img_arr = np.array(img_rgb, dtype=np.float32) / 255.0
        return np.expand_dims(img_arr, axis=0)

    def predict(
        self, 
        input_source: Union[str, Image.Image, np.ndarray],
        threshold: float = 0.28,
        min_slick_pixels: int = 35
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()

        x = self.preprocess(input_source)
        raw_pred = self.model.predict(x, verbose=0)[0]

        prob_oil = raw_pred[:, :, 1] + raw_pred[:, :, 2]
        spill_mask = prob_oil > threshold
        spill_pixel_count = int(np.sum(spill_mask))
        total_pixels = 256 * 256

        spill_detected = bool(spill_pixel_count >= min_slick_pixels)
        spill_area_pct = round(float((spill_pixel_count / total_pixels) * 100.0), 2)
        
        if spill_detected:
            confidence = round(float(np.mean(prob_oil[spill_mask])) * 100.0, 1)
        else:
            confidence = round(float(np.max(prob_oil)) * 100.0, 1)

        anomaly_prob_matrix = np.round(prob_oil.astype(np.float32), 4)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return {
            "spill_detected": spill_detected,
            "confidence": confidence,
            "spill_mask": spill_mask,
            "spill_area_pct": spill_area_pct,
            "anomaly_probability": anomaly_prob_matrix,
            "inference_time_ms": elapsed_ms
        }
