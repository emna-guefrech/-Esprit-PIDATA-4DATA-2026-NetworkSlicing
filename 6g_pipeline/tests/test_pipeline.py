"""
tests/test_pipeline.py
Basic tests for the 6G ML pipeline functions.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model_pipeline import safe_sigmoid, save_model, load_model


# ── Test 1: safe_sigmoid ──────────────────────────────────────────────
def test_safe_sigmoid_range():
    """Output must always be in (0, 1)."""
    values = np.array([-100, -10, -1, 0, 1, 10, 100])
    result = safe_sigmoid(values)
    assert (result > 0).all(), "sigmoid output must be > 0"
    assert (result < 1).all(), "sigmoid output must be < 1"


def test_safe_sigmoid_zero():
    """sigmoid(0) must equal 0.5."""
    assert abs(safe_sigmoid(0) - 0.5) < 1e-6


def test_safe_sigmoid_positive():
    """Positive input must give output > 0.5."""
    assert safe_sigmoid(1) > 0.5


def test_safe_sigmoid_negative():
    """Negative input must give output < 0.5."""
    assert safe_sigmoid(-1) < 0.5


# ── Test 2: save_model / load_model ──────────────────────────────────
def test_save_and_load_model(tmp_path):
    """Object saved then loaded must equal the original."""
    obj  = {"key": [1, 2, 3], "score": 0.95}
    path = str(tmp_path / "test_obj.joblib")
    save_model(obj, path)
    loaded = load_model(path)
    assert loaded == obj


def test_save_model_creates_file(tmp_path):
    """save_model must create the file on disk."""
    path = str(tmp_path / "subdir" / "model.joblib")
    save_model([1, 2, 3], path)
    assert os.path.exists(path)


# ── Test 3: dataset files exist ───────────────────────────────────────
def test_congestion_csv_exists():
    assert os.path.exists("network_slicing_congestion_final.csv"), \
        "network_slicing_congestion_final.csv not found — run 'make prepare' first"


def test_congestion_csv_not_empty():
    df = pd.read_csv("network_slicing_congestion_final.csv", encoding="utf-8")
    assert len(df) > 0, "Congestion CSV is empty"
    assert len(df.columns) > 0, "Congestion CSV has no columns"


# ── Test 4: model files exist after training ──────────────────────────
def test_model_dso1_exists():
    assert os.path.exists("models/model_dso1_regression.joblib"), \
        "DSO1 model not found — run 'make train' first"


def test_model_dso52_exists():
    assert os.path.exists("models/model_dso52_isoforest.joblib"), \
        "DSO5.2 model not found — run 'make train' first"


def test_model_dso53_exists():
    assert os.path.exists("models/model_dso53_sgd.joblib"), \
        "DSO5.3 model not found — run 'make train' first"
