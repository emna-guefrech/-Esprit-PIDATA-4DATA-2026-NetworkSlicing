"""
tests/test_pipeline.py
======================
Basic tests for the 5G pipeline functions.
"""

import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from model_pipeline import (
    prepare_data,
    train_model,
    evaluate_model,
    save_model,
    load_model,
    _engineer_features_rf,
    inject_noise,
    augment_features,
    build_anomaly_labels,
    NOISE_CONFIG,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def raw_data():
    """Load a small sample of the raw datasets for testing."""
    train = pd.read_csv("train_dataset.csv").drop_duplicates().head(500)
    test  = pd.read_csv("test_dataset.csv").drop_duplicates().head(200)
    return train, test


@pytest.fixture(scope="module")
def prepared():
    """Run prepare_data() once and reuse across tests."""
    return prepare_data(
        train_path="train_dataset.csv",
        test_path="test_dataset.csv",
    )


@pytest.fixture(scope="module")
def trained_model(prepared):
    """Train a small RF model for testing."""
    return train_model(
        X_tr=prepared["X_tr"],
        y_tr=prepared["y_tr"],
        n_estimators=10,
    )


# ── Tests: prepare_data ───────────────────────────────────────────────────────

def test_prepare_data_returns_dict(prepared):
    assert isinstance(prepared, dict)


def test_prepare_data_keys(prepared):
    expected_keys = ["X_tr", "y_tr", "X_val", "y_val",
                     "X_test", "scaler", "train_raw", "test_raw"]
    for key in expected_keys:
        assert key in prepared, f"Missing key: {key}"


def test_prepare_data_shapes(prepared):
    assert prepared["X_tr"].shape[1]  == 9, "Expected 9 features"
    assert prepared["X_val"].shape[1] == 9, "Expected 9 features"
    assert prepared["X_test"].shape[1] == 9, "Expected 9 features"
    assert len(prepared["X_tr"]) == len(prepared["y_tr"])
    assert len(prepared["X_val"]) == len(prepared["y_val"])


def test_prepare_data_no_nulls(prepared):
    assert not np.isnan(prepared["X_tr"]).any(),  "NaN in X_tr"
    assert not np.isnan(prepared["X_val"]).any(), "NaN in X_val"
    assert not np.isnan(prepared["X_test"]).any(), "NaN in X_test"


def test_prepare_data_labels(prepared):
    unique_labels = set(prepared["y_tr"])
    assert unique_labels == {1, 2, 3}, f"Unexpected labels: {unique_labels}"


def test_prepare_data_split_ratio(prepared):
    total = len(prepared["X_tr"]) + len(prepared["X_val"])
    val_ratio = len(prepared["X_val"]) / total
    assert 0.18 <= val_ratio <= 0.22, f"Unexpected split ratio: {val_ratio:.2f}"


# ── Tests: feature engineering ────────────────────────────────────────────────

def test_engineer_features_rf_columns(raw_data):
    train, _ = raw_data
    features = _engineer_features_rf(train)
    expected = ["time_sin", "time_cos", "is_peak", "log_plr",
                "log_delay", "plr_x_delay", "lte5g_cat",
                "high_delay", "high_plr"]
    for col in expected:
        assert col in features.columns, f"Missing feature: {col}"


def test_engineer_features_rf_no_nulls(raw_data):
    train, _ = raw_data
    features = _engineer_features_rf(train)
    assert not features.isnull().any().any(), "NaN in engineered features"


def test_time_sin_cos_range(raw_data):
    train, _ = raw_data
    features = _engineer_features_rf(train)
    assert features["time_sin"].between(-1, 1).all()
    assert features["time_cos"].between(-1, 1).all()


# ── Tests: train_model ────────────────────────────────────────────────────────

def test_train_model_returns_classifier(trained_model):
    from sklearn.ensemble import RandomForestClassifier
    assert isinstance(trained_model, RandomForestClassifier)


def test_train_model_can_predict(trained_model, prepared):
    preds = trained_model.predict(prepared["X_val"])
    assert len(preds) == len(prepared["y_val"])
    assert set(preds).issubset({1, 2, 3})


# ── Tests: evaluate_model ─────────────────────────────────────────────────────

def test_evaluate_model_returns_dict(trained_model, prepared):
    result = evaluate_model(
        model=trained_model,
        X_val=prepared["X_val"],
        y_val=prepared["y_val"],
    )
    assert isinstance(result, dict)
    assert "accuracy"  in result
    assert "f1_macro"  in result


def test_evaluate_model_accuracy_range(trained_model, prepared):
    result = evaluate_model(
        model=trained_model,
        X_val=prepared["X_val"],
        y_val=prepared["y_val"],
    )
    assert 0.0 <= result["accuracy"] <= 1.0
    assert 0.0 <= result["f1_macro"] <= 1.0


# ── Tests: save and load model ────────────────────────────────────────────────

def test_save_and_load_model(trained_model, prepared, tmp_path):
    model_path  = str(tmp_path / "test_model.pkl")
    scaler_path = str(tmp_path / "test_scaler.pkl")

    save_model(
        model=trained_model,
        scaler=prepared["scaler"],
        model_path=model_path,
        scaler_path=scaler_path,
    )

    loaded_model, loaded_scaler = load_model(
        model_path=model_path,
        scaler_path=scaler_path,
    )

    preds_original = trained_model.predict(prepared["X_val"])
    preds_loaded   = loaded_model.predict(prepared["X_val"])
    assert np.array_equal(preds_original, preds_loaded), \
        "Loaded model predictions differ from original"


# ── Tests: noise injection ────────────────────────────────────────────────────

def test_inject_noise_adds_columns(raw_data):
    train, _ = raw_data
    noisy = inject_noise(train, NOISE_CONFIG)
    expected_cols = ["network_load_factor", "packet_delay_noisy",
                     "packet_loss_noisy", "qos_strictness",
                     "p_sla_violation", "sla_met"]
    for col in expected_cols:
        assert col in noisy.columns, f"Missing noise column: {col}"


def test_inject_noise_sla_met_binary(raw_data):
    train, _ = raw_data
    noisy = inject_noise(train, NOISE_CONFIG)
    assert set(noisy["sla_met"].unique()).issubset({0, 1})


def test_inject_noise_load_factor_range(raw_data):
    train, _ = raw_data
    noisy = inject_noise(train, NOISE_CONFIG)
    assert noisy["network_load_factor"].between(0, 1).all()


# ── Tests: anomaly labels ─────────────────────────────────────────────────────

def test_build_anomaly_labels_binary(raw_data):
    train, _ = raw_data
    labels = build_anomaly_labels(train)
    assert set(labels.unique()).issubset({0, 1})


def test_build_anomaly_labels_length(raw_data):
    train, _ = raw_data
    labels = build_anomaly_labels(train)
    assert len(labels) == len(train)
