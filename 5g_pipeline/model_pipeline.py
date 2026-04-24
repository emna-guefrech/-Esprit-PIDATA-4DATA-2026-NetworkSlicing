"""
model_pipeline.py
=================
Full modular ML pipeline for 5G Network Slice Classification.
Covers all 4 modeling approaches from the notebook:

    1. Data Preparation      : prepare_data()
    2. Random Forest         : train_model(), evaluate_model()
    3. XGBoost + SLA Risk    : inject_noise(), augment_features(),
                               train_xgboost(), evaluate_xgboost()
    4. Anomaly Detection     : build_anomaly_labels(), train_anomaly_models(),
                               evaluate_anomaly_models()
    5. Online Learning (HAT) : train_online_model(), evaluate_online_model()
    6. Model I/O             : save_model(), load_model()
"""

import warnings

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib
import mlflow
import mlflow.sklearn
import os
from datetime import datetime, timezone
from elasticsearch import Elasticsearch

# ── Elasticsearch client ──────────────────────────────────────────
ES_CLIENT = None

def _get_es_client():
    """Get or create Elasticsearch client."""
    global ES_CLIENT
    if ES_CLIENT is None:
        try:
            ES_CLIENT = Elasticsearch("http://localhost:9200")
            if ES_CLIENT.ping():
                print("[ES] Connected to Elasticsearch ✅")
            else:
                print("[ES] Elasticsearch not reachable ⚠️")
                ES_CLIENT = None
        except Exception as e:
            print(f"[ES] Connection failed: {e} ⚠️")
            ES_CLIENT = None
    return ES_CLIENT


def _log_to_es(index: str, doc: dict):
    """Send a log document to Elasticsearch."""
    es = _get_es_client()
    if es is None:
        return
    try:
        doc["@timestamp"] = datetime.now(timezone.utc).isoformat()
        doc["pipeline"]   = "5G"
        es.index(index=index, document=doc)
    except Exception as e:
        print(f"[ES] Failed to log: {e}")

# ── Sklearn ───────────────────────────────────────────────────────────────────
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
)
from sklearn.utils.class_weight import compute_class_weight

# ── XGBoost ───────────────────────────────────────────────────────────────────
import xgboost as xgb

# ── River (online learning) ───────────────────────────────────────────────────
from river import tree, metrics, preprocessing, drift
from river.utils import Rolling

# ── Constants ─────────────────────────────────────────────────────────────────
TARGET = "slice Type"
BASE_FEATURES = ["Time", "Packet Loss Rate", "Packet delay", "LTE/5g Category"]
FEAT_NAMES = [
    "time_sin",
    "time_cos",
    "is_peak",
    "log_plr",
    "log_delay",
    "plr_x_delay",
    "lte5g_cat",
    "high_delay",
    "high_plr",
]
USE_CASE_COLS = [
    "AR/VR/Gaming",
    "Healthcare",
    "Industry 4.0",
    "IoT Devices",
    "Public Safety",
    "Smart City & Home",
    "Smart Transportation",
    "Smartphone",
]
SLICE_NAMES = {1: "eMBB", 2: "URLLC", 3: "mIoT"}
RANDOM_STATE = 42

NOISE_CONFIG = {
    "congestion_base": 0.15,
    "congestion_peak_add": 0.25,
    "congestion_noise_std": 0.08,
    "delay_noise_std": 0.12,
    "loss_noise_std": 0.10,
    "flip_base_rate": 0.05,
    "flip_strictness_mult": 0.20,
    "flip_load_mult": 0.15,
}

PLR_RISK_MAP = {1e-6: 1.0, 1e-3: 0.5, 1e-2: 0.0}
DELAY_RISK_MAP = {10: 1.0, 50: 0.8, 60: 0.7, 75: 0.6, 100: 0.4, 150: 0.2, 300: 0.0}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DATA PREPARATION
# ═══════════════════════════════════════════════════════════════════════════════


def _engineer_features_rf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive 9 interpretable features from the 4 base QoS columns.
    Used by Random Forest and Online Learning pipelines.
    """
    t = df["Time"]
    plr = df["Packet Loss Rate"]
    delay = df["Packet delay"]
    cat = df["LTE/5g Category"]

    return pd.DataFrame(
        {
            "time_sin": np.sin(2 * np.pi * t / 24),
            "time_cos": np.cos(2 * np.pi * t / 24),
            "is_peak": (((t >= 8) & (t <= 10)) | ((t >= 18) & (t <= 21))).astype(int),
            "log_plr": np.log10(plr.clip(1e-9)),
            "log_delay": np.log10(delay),
            "plr_x_delay": np.log10(plr.clip(1e-9)) * np.log10(delay),
            "lte5g_cat": cat.astype(float),
            "high_delay": (delay >= 150).astype(int),
            "high_plr": (plr >= 1e-2).astype(int),
        },
        index=df.index,
    )


def _engineer_features_xgb(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering for XGBoost / anomaly detection pipelines.
    Drops redundant columns and adds domain-specific features.
    """
    df = df.copy()

    # Drop perfectly anti-correlated columns
    df.drop(columns=[c for c in ["LTE/5G", "Non-GBR"] if c in df.columns], inplace=True)

    # Cyclic time + peak flag
    df["time_sin"] = np.sin(2 * np.pi * df["Time"] / 24)
    df["time_cos"] = np.cos(2 * np.pi * df["Time"] / 24)
    df["is_peak"] = (
        ((df["Time"] >= 8) & (df["Time"] <= 10))
        | ((df["Time"] >= 18) & (df["Time"] <= 21))
    ).astype(int)

    # Log-scale QoS
    df["log_plr"] = np.log10(df["Packet Loss Rate"].clip(1e-9))
    df["log_delay"] = np.log10(df["Packet delay"])

    # QoS strictness score
    plr_r = df["Packet Loss Rate"].map(PLR_RISK_MAP).fillna(0.5)
    dly_r = df["Packet delay"].map(DELAY_RISK_MAP).fillna(0.5)
    df["qos_strictness"] = 0.6 * plr_r + 0.4 * dly_r

    # Interaction features
    df["gbr_x_strict"] = df["GBR"] * df["qos_strictness"]
    df["peak_x_strict"] = df["is_peak"] * df["qos_strictness"]

    # Use-case aggregation
    uc = [c for c in USE_CASE_COLS if c in df.columns]
    df["n_use_cases"] = df[uc].sum(axis=1)
    df["is_mc"] = (
        df[
            [
                c
                for c in ["Healthcare", "Public Safety", "Smart Transportation"]
                if c in df.columns
            ]
        ]
        .max(axis=1)
        .astype(int)
    )
    df["is_consumer"] = (
        df[[c for c in ["Smartphone", "AR/VR/Gaming"] if c in df.columns]]
        .max(axis=1)
        .astype(int)
    )
    df["is_industrial"] = (
        df[
            [
                c
                for c in ["Industry 4.0", "IoT Devices", "Smart City & Home"]
                if c in df.columns
            ]
        ]
        .max(axis=1)
        .astype(int)
    )
    return df


def prepare_data(
    train_path: str = "train_dataset.csv",
    test_path: str = "test_dataset.csv",
    test_size: float = 0.20,
    random_state: int = RANDOM_STATE,
) -> dict:
    """
    Load raw CSVs, remove duplicates, engineer features, scale, and split.

    Returns
    -------
    dict with keys:
        X_tr, y_tr, X_val, y_val, X_test : numpy arrays
        scaler                            : fitted StandardScaler
        train_raw, test_raw               : cleaned DataFrames (needed downstream)
        feature_names                     : list of feature names
    """
    print("[prepare_data] Loading raw datasets...")
    train_raw = pd.read_csv(train_path)
    test_raw = pd.read_csv(test_path)

    print(f"[prepare_data] Train shape before cleaning : {train_raw.shape}")
    print(f"[prepare_data] Test  shape before cleaning : {test_raw.shape}")

    # Remove duplicates
    dup_train = train_raw.duplicated().sum()
    dup_test = test_raw.duplicated().sum()
    train_raw = train_raw.drop_duplicates().reset_index(drop=True)
    test_raw = test_raw.drop_duplicates().reset_index(drop=True)

    print(f"[prepare_data] Removed {dup_train:,} duplicate rows from train")
    print(f"[prepare_data] Removed {dup_test:,} duplicate rows from test")
    print(f"[prepare_data] Train shape after cleaning  : {train_raw.shape}")
    print(f"[prepare_data] Test  shape after cleaning  : {test_raw.shape}")

    # Feature engineering (RF features)
    X_all = _engineer_features_rf(train_raw)
    y_all = train_raw[TARGET].values
    X_test_eng = _engineer_features_rf(test_raw)

    # Scale (fit on train only)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    X_test_s = scaler.transform(X_test_eng)

    # Train / validation split
    X_tr, X_val, y_tr, y_val = train_test_split(
        X_scaled,
        y_all,
        test_size=test_size,
        stratify=y_all,
        random_state=random_state,
    )

    print(f"[prepare_data] X_tr  : {X_tr.shape}  | y_tr  : {y_tr.shape}")
    print(f"[prepare_data] X_val : {X_val.shape} | y_val : {y_val.shape}")
    print(f"[prepare_data] X_test: {X_test_s.shape}")
    print("[prepare_data] Done ✅\n")

    return {
        "X_tr": X_tr,
        "y_tr": y_tr,
        "X_val": X_val,
        "y_val": y_val,
        "X_test": X_test_s,
        "scaler": scaler,
        "train_raw": train_raw,
        "test_raw": test_raw,
        "feature_names": FEAT_NAMES,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — RANDOM FOREST CLASSIFIER
# ═══════════════════════════════════════════════════════════════════════════════


def train_model(
    X_tr: np.ndarray,
    y_tr: np.ndarray,
    n_estimators: int = 200,
    max_depth: int    = None,
    random_state: int = RANDOM_STATE,
) -> RandomForestClassifier:
    """
    Train a Random Forest classifier for slice type prediction.
    Logs params, metrics and model to MLflow.

    Returns
    -------
    Fitted RandomForestClassifier
    """
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_RandomForest_SliceClassification")

    with mlflow.start_run(run_name="RF_train"):
        print("[train_model] Training Random Forest...")
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,
        )
        model.fit(X_tr, y_tr)

        # Log hyperparameters
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        mlflow.log_param("random_state", random_state)
        mlflow.log_param("train_size", X_tr.shape[0])
        mlflow.log_param("n_features", X_tr.shape[1])

        # Log training accuracy
        train_preds = model.predict(X_tr)
        train_acc   = accuracy_score(y_tr, train_preds)
        train_f1    = f1_score(y_tr, train_preds, average="macro")
        mlflow.log_metric("train_accuracy", round(train_acc, 4))
        mlflow.log_metric("train_f1_macro", round(train_f1, 4))

        # Log model
        mlflow.sklearn.log_model(model, artifact_path="random_forest_model")

        print(f"[train_model] Train accuracy : {train_acc:.4f}")
        print(f"[train_model] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":   "5G_RandomForest_SliceClassification",
            "run_name":     "RF_train",
            "model":        "RandomForest",
            "n_estimators": n_estimators,
            "max_depth":    str(max_depth),
            "train_accuracy": round(train_acc, 4),
            "train_f1":       round(train_f1, 4),
            "type":         "training",
        })

    print("[train_model] Done ✅\n")
    return model

def evaluate_model(
    model: RandomForestClassifier,
    X_val: np.ndarray,
    y_val: np.ndarray,
) -> dict:
    """
    Evaluate the Random Forest on the validation set.
    Logs validation metrics to MLflow.

    Returns
    -------
    dict with accuracy, f1_macro, report, confusion_matrix
    """
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_RandomForest_SliceClassification")

    print("[evaluate_model] Evaluating Random Forest...")
    y_pred   = model.predict(X_val)
    acc      = accuracy_score(y_val, y_pred)
    f1_macro = f1_score(y_val, y_pred, average="macro")
    report   = classification_report(
        y_val, y_pred,
        target_names=[SLICE_NAMES[k] for k in sorted(SLICE_NAMES)],
    )
    cm = confusion_matrix(y_val, y_pred)

    with mlflow.start_run(run_name="RF_evaluate"):
        mlflow.log_metric("val_accuracy", round(acc, 4))
        mlflow.log_metric("val_f1_macro", round(f1_macro, 4))
        mlflow.log_metric("val_size",     len(y_val))
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":    "5G_RandomForest_SliceClassification",
            "run_name":      "RF_evaluate",
            "model":         "RandomForest",
            "val_accuracy":  round(acc, 4),
            "val_f1_macro":  round(f1_macro, 4),
            "type":          "evaluation",
        })

    print(f"\n{'='*50}")
    print(f"  Accuracy  : {acc:.4f}")
    print(f"  F1-macro  : {f1_macro:.4f}")
    print(f"{'='*50}")
    print("\nClassification Report:")
    print(report)
    print("Confusion Matrix:")
    print(cm)
    print("[evaluate_model] MLflow metrics logged ✅")
    print("[evaluate_model] Done ✅\n")

    return {
        "accuracy":         acc,
        "f1_macro":         f1_macro,
        "report":           report,
        "confusion_matrix": cm,
    }
        
# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — XGBOOST + SLA RISK SCORING
# ═══════════════════════════════════════════════════════════════════════════════


def inject_noise(
    df: pd.DataFrame,
    config: dict = NOISE_CONFIG,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """
    Inject synthetic network uncertainty into the dataset.
    Adds: network_load_factor, packet_delay_noisy, packet_loss_noisy,
          qos_strictness, p_sla_violation, sla_met.
    """
    rng = np.random.default_rng(random_state)
    df = df.copy()
    n = len(df)

    # Network congestion factor
    time_col = df["Time"] if "Time" in df.columns else pd.Series(np.zeros(n))
    is_peak_hour = ((time_col >= 8) & (time_col <= 10)) | (
        (time_col >= 18) & (time_col <= 21)
    )
    congestion = (
        config["congestion_base"]
        + is_peak_hour.values * config["congestion_peak_add"]
        + rng.normal(0, config["congestion_noise_std"], n)
    ).clip(0, 1)
    df["network_load_factor"] = congestion

    # QoS parameter drift
    delay_nominal = df["Packet delay"].values.astype(float)
    delay_noise = rng.normal(0, config["delay_noise_std"], n) * delay_nominal
    df["packet_delay_noisy"] = (delay_nominal + delay_noise).clip(1, None)

    log_loss_nominal = np.log10(df["Packet Loss Rate"].values.astype(float))
    log_loss_noise = rng.normal(0, config["loss_noise_std"], n)
    df["packet_loss_noisy"] = np.power(10, log_loss_nominal + log_loss_noise).clip(
        1e-8, 1.0
    )

    # QoS strictness score
    plr_risk = df["Packet Loss Rate"].map({1e-6: 1.0, 1e-3: 0.5, 1e-2: 0.0}).fillna(0.5)
    delay_risk = df["Packet delay"].map(DELAY_RISK_MAP).fillna(0.5)
    strictness = 0.60 * plr_risk + 0.40 * delay_risk
    df["qos_strictness"] = strictness

    # SLA violation probability
    p_violation = (
        config["flip_base_rate"]
        + strictness * config["flip_strictness_mult"]
        + congestion * config["flip_load_mult"]
    ).clip(0, 0.70)
    df["p_sla_violation"] = p_violation

    # SLA met / violated label
    flip_mask = rng.random(n) < p_violation.values
    df["sla_met"] = (~flip_mask).astype(int)

    return df


def augment_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add QoS-vs-load interaction features.
    Requires inject_noise() to have been called first.
    """
    df = df.copy()
    df["load_induced_delay"] = df["network_load_factor"] * 100
    df["delay_margin"] = df["Packet delay"] - df["load_induced_delay"]
    df["delay_margin_pct"] = df["delay_margin"] / df["Packet delay"].replace(0, np.nan)
    df["effective_loss_rate"] = df["packet_loss_noisy"] * (
        1 + df["network_load_factor"]
    )
    df["loss_margin"] = df["Packet Loss Rate"] - df["effective_loss_rate"]
    df["violation_risk_composite"] = df["qos_strictness"] * df["network_load_factor"]
    df["delay_margin_ok"] = (df["delay_margin"] > 0).astype(int)
    df["loss_margin_ok"] = (df["loss_margin"] > 0).astype(int)
    df["n_margins_ok"] = df["delay_margin_ok"] + df["loss_margin_ok"]
    return df


def train_xgboost(
    train_raw: pd.DataFrame,
    test_raw: pd.DataFrame,
    random_state: int = RANDOM_STATE,
) -> dict:
    """
    Train a calibrated XGBoost classifier for binary SLA risk prediction.
    Applies noise injection, feature augmentation, class weighting,
    and probability calibration.

    Returns
    -------
    dict with keys:
        model         : final calibrated XGBoost model
        X_val, y_val  : validation arrays
        features      : list of feature names used
        results       : AUC, Brier, LogLoss metrics
    """
    print("[train_xgboost] Injecting noise and augmenting features...")

    train_noisy = inject_noise(train_raw, NOISE_CONFIG, random_state)
    test_noisy = inject_noise(test_raw, NOISE_CONFIG, random_state + 1)
    train_aug = augment_features(train_noisy)
    test_aug = augment_features(test_noisy)

    # Define feature set
    EXCLUDE = [
        "slice Type",
        "sla_met",
        "p_sla_violation",
        "strictness_bin",
        "LTE/5g Category_scaled",
        "Time_scaled",
        "Packet Loss Rate_scaled",
        "Packet delay_scaled",
        "log_packet_loss_scaled",
        "log_packet_delay_scaled",
    ]
    EXCLUDE = [c for c in EXCLUDE if c in train_aug.columns]
    FEATURES = [c for c in train_aug.columns if c not in EXCLUDE]
    TARGET_B = "sla_met"

    X = train_aug[FEATURES].copy()
    y = train_aug[TARGET_B].copy()

    # Class weights
    classes = np.array([0, 1])
    cw = compute_class_weight("balanced", classes=classes, y=y)
    cw_dict = dict(zip(classes, cw))
    sw_all = np.array([cw_dict[c] for c in y])

    # Train / val split
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y, test_size=0.20, random_state=random_state, stratify=y
    )

    print("[train_xgboost] Training XGBoost with calibration...")

    best_params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "n_estimators": 300,
        "learning_rate": 0.05,
        "max_depth": 5,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": random_state,
        "n_jobs": -1,
        "verbosity": 0,
    }

    # Calibration
    cal_results = {}
    for method in ["sigmoid", "isotonic"]:
        cal_model = CalibratedClassifierCV(
            xgb.XGBClassifier(**best_params), method=method, cv=3
        )
        cal_model.fit(X, y, **{"sample_weight": sw_all})
        proba_val = cal_model.predict_proba(X_val)[:, 1]
        cal_results[method] = {
            "model": cal_model,
            "brier": brier_score_loss(y_val, proba_val),
            "logloss": log_loss(y_val, proba_val),
            "auc": roc_auc_score(y_val, proba_val),
            "proba_val": proba_val,
        }

    best_method = min(cal_results, key=lambda k: cal_results[k]["brier"])
    final_model = cal_results[best_method]["model"]
    proba_val = cal_results[best_method]["proba_val"]

    auc = cal_results[best_method]["auc"]
    brier = cal_results[best_method]["brier"]
    ll = cal_results[best_method]["logloss"]

    print(f"\n{'='*50}")
    print(f"  Best calibration : {best_method}")
    print(f"  AUC-ROC          : {auc:.4f}")
    print(f"  Brier Score      : {brier:.4f}")
    print(f"  Log Loss         : {ll:.4f}")
    print(f"{'='*50}")

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_XGBoost_SLARisk")
    with mlflow.start_run(run_name="XGB_train"):
        mlflow.log_param("calibration_method", best_method)
        mlflow.log_param("n_estimators",        best_params["n_estimators"])
        mlflow.log_param("max_depth",           best_params["max_depth"])
        mlflow.log_param("learning_rate",       best_params["learning_rate"])
        mlflow.log_metric("auc_roc",            round(auc,   4))
        mlflow.log_metric("brier_score",        round(brier, 4))
        mlflow.log_metric("log_loss",           round(ll,    4))
        print("[train_xgboost] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":         "5G_XGBoost_SLARisk",
            "run_name":           "XGB_train",
            "model":              "XGBoost",
            "calibration_method": best_method,
            "auc_roc":            round(auc,   4),
            "brier_score":        round(brier, 4),
            "log_loss":           round(ll,    4),
            "type":               "training",
        })

    print("[train_xgboost] Done ✅\n")

    return {
        "model": final_model,
        "X_val": X_val,
        "y_val": y_val,
        "features": FEATURES,
        "results": {"auc": auc, "brier": brier, "logloss": ll},
    }


def evaluate_xgboost(
    model,
    X_val: pd.DataFrame,
    y_val: pd.Series,
) -> dict:
    """
    Evaluate the XGBoost SLA risk model and print metrics.

    Returns
    -------
    dict with auc, brier, logloss, classification report
    """
    print("[evaluate_xgboost] Evaluating XGBoost SLA risk model...")

    proba = model.predict_proba(X_val)[:, 1]
    pred = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y_val, proba)
    brier = brier_score_loss(y_val, proba)
    ll = log_loss(y_val, proba)
    report = classification_report(
        y_val, pred, target_names=["SLA violated", "SLA met"]
    )

    print(f"\n{'='*50}")
    print(f"  AUC-ROC    : {auc:.4f}")
    print(f"  Brier Score: {brier:.4f}")
    print(f"  Log Loss   : {ll:.4f}")
    print(f"{'='*50}")
    print("\nClassification Report:")
    print(report)

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_XGBoost_SLARisk")
    with mlflow.start_run(run_name="XGB_evaluate"):
        mlflow.log_metric("val_auc_roc",    round(auc,   4))
        mlflow.log_metric("val_brier_score",round(brier, 4))
        mlflow.log_metric("val_log_loss",   round(ll,    4))
        print("[evaluate_xgboost] MLflow run logged ✅")

    print("[evaluate_xgboost] Done ✅\n")

    return {"auc": auc, "brier": brier, "logloss": ll, "report": report}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


def build_anomaly_labels(df: pd.DataFrame) -> pd.Series:
    """
    Derive binary anomaly ground-truth labels from 5G domain rules:
        R1: GBR premium traffic with high packet loss  (PLR >= 1e-2)
        R2: GBR premium traffic with high latency in eMBB/URLLC slices
        R3: Slice 2 (URLLC) IoT traffic without GBR guarantee

    Returns
    -------
    pd.Series of 0/1 labels
    """
    y = pd.Series(0, index=df.index, dtype=int)
    y[(df["GBR"] == 1) & (df["Packet Loss Rate"] >= 1e-2)] = 1
    if "slice Type" in df.columns:
        y[
            (df["GBR"] == 1)
            & (df["Packet delay"] >= 150)
            & (df["slice Type"].isin([1, 2]))
        ] = 1
        y[(df["slice Type"] == 2) & (df["GBR"] == 0)] = 1
    return y


def train_anomaly_models(
    train_raw: pd.DataFrame,
    test_raw: pd.DataFrame,
    random_state: int = RANDOM_STATE,
) -> dict:
    """
    Train an ensemble of anomaly detection models:
        - Isolation Forest
        - One-Class SVM
        - PCA-based Autoencoder (reconstruction error)

    Fuses their scores using AUC²-proportional weights.

    Returns
    -------
    dict with:
        models         : dict of individual fitted models
        ensemble_scores: normalised ensemble anomaly scores (train)
        test_scores    : ensemble anomaly scores (test)
        y_labels       : ground-truth anomaly labels (train)
        best_threshold : optimal decision threshold (max F1)
        metrics        : AUC, AP per model and ensemble
    """
    print("[train_anomaly_models] Building anomaly labels...")

    # Feature engineering
    ANOMALY_FEATURES = [
        "LTE/5g Category",
        "time_sin",
        "time_cos",
        "is_peak",
        "log_plr",
        "log_delay",
        "qos_strictness",
        "IoT",
        "GBR",
        "gbr_x_strict",
        "peak_x_strict",
        "n_use_cases",
        "is_mc",
        "is_consumer",
        "is_industrial",
    ] + [c for c in USE_CASE_COLS]

    train_eng = _engineer_features_xgb(train_raw)
    test_eng = _engineer_features_xgb(test_raw)

    ANOMALY_FEATURES = [c for c in ANOMALY_FEATURES if c in train_eng.columns]

    y_labels = build_anomaly_labels(train_raw)
    train_eng["is_anomaly"] = y_labels

    n_anom = y_labels.sum()
    print(
        f"[train_anomaly_models] Anomalies: {n_anom:,} / {len(y_labels):,} "
        f"({n_anom/len(y_labels)*100:.1f}%)"
    )

    # Scale
    scaler_rob = RobustScaler()
    Xtr_s = scaler_rob.fit_transform(train_eng[ANOMALY_FEATURES])
    Xte_s = scaler_rob.transform(test_eng[ANOMALY_FEATURES])

    CONTAMINATION = float(y_labels.mean())
    X_normal = Xtr_s[y_labels == 0]

    # ── Isolation Forest ─────────────────────────────────────────────────────
    print("[train_anomaly_models] Training Isolation Forest...")
    best_if_auc, best_if = 0, None
    for n_est in [100, 200, 300]:
        for max_feat in [0.6, 0.8, 1.0]:
            m = IsolationForest(
                n_estimators=n_est,
                max_features=max_feat,
                contamination=CONTAMINATION,
                random_state=random_state,
                n_jobs=-1,
            )
            m.fit(Xtr_s)
            sc = -m.score_samples(Xtr_s)
            auc = roc_auc_score(y_labels, sc)
            if auc > best_if_auc:
                best_if_auc = auc
                best_if = m

    sIF_tr = -best_if.score_samples(Xtr_s)
    sIF_te = -best_if.score_samples(Xte_s)
    mn, mx = sIF_tr.min(), sIF_tr.max()
    sIF_tr = (sIF_tr - mn) / (mx - mn)
    sIF_te = (sIF_te - mn) / (mx - mn)

    # ── One-Class SVM ────────────────────────────────────────────────────────
    print("[train_anomaly_models] Training One-Class SVM...")
    best_oc_auc, best_oc = 0, None
    for gamma in ["scale", "auto", 0.1]:
        for nu in [CONTAMINATION * 0.5, CONTAMINATION, min(CONTAMINATION * 1.5, 0.49)]:
            m = OneClassSVM(kernel="rbf", nu=nu, gamma=gamma)
            m.fit(X_normal)
            sc = -m.decision_function(Xtr_s)
            try:
                auc = roc_auc_score(y_labels, sc)
                if auc > best_oc_auc:
                    best_oc_auc = auc
                    best_oc = m
            except Exception:
                pass

    sOC_tr = -best_oc.decision_function(Xtr_s)
    sOC_te = -best_oc.decision_function(Xte_s)
    mn, mx = sOC_tr.min(), sOC_tr.max()
    sOC_tr = (sOC_tr - mn) / (mx - mn)
    sOC_te = (sOC_te - mn) / (mx - mn)

    # ── PCA Autoencoder ───────────────────────────────────────────────────────
    print("[train_anomaly_models] Training PCA Autoencoder...")
    best_ae_auc, best_ae = 0, None
    for n_comp in [4, 6, 8, 10, 12, 15]:
        pca = PCA(n_components=n_comp, random_state=random_state)
        pca.fit(X_normal)
        sc = np.mean((Xtr_s - pca.inverse_transform(pca.transform(Xtr_s))) ** 2, axis=1)
        auc = roc_auc_score(y_labels, sc)
        if auc > best_ae_auc:
            best_ae_auc = auc
            best_ae = pca

    sAE_tr = np.mean(
        (Xtr_s - best_ae.inverse_transform(best_ae.transform(Xtr_s))) ** 2, axis=1
    )
    sAE_te = np.mean(
        (Xte_s - best_ae.inverse_transform(best_ae.transform(Xte_s))) ** 2, axis=1
    )
    mn, mx = sAE_tr.min(), sAE_tr.max()
    sAE_tr = (sAE_tr - mn) / (mx - mn)
    sAE_te = (sAE_te - mn) / (mx - mn)

    # ── Ensemble fusion ───────────────────────────────────────────────────────
    print("[train_anomaly_models] Fusing ensemble scores...")
    model_aucs = np.array(
        [
            roc_auc_score(y_labels, sIF_tr),
            roc_auc_score(y_labels, sOC_tr),
            roc_auc_score(y_labels, sAE_tr),
        ]
    )
    weights = model_aucs**2
    weights /= weights.sum()

    ens_tr = np.column_stack([sIF_tr, sOC_tr, sAE_tr]) @ weights
    ens_te = np.column_stack([sIF_te, sOC_te, sAE_te]) @ weights
    mn, mx = ens_tr.min(), ens_tr.max()
    ens_tr = (ens_tr - mn) / (mx - mn)
    ens_te = (ens_te - mn) / (mx - mn)

    # Best threshold
    thresholds = np.linspace(0.01, 0.99, 200)
    f1_scores = [
        f1_score(y_labels, (ens_tr >= t).astype(int), zero_division=0)
        for t in thresholds
    ]
    best_thresh = float(thresholds[int(np.argmax(f1_scores))])

    ens_auc = roc_auc_score(y_labels, ens_tr)
    ens_ap = average_precision_score(y_labels, ens_tr)

    print(f"\n{'='*50}")
    print(f"  IF  AUC : {model_aucs[0]:.4f}")
    print(f"  SVM AUC : {model_aucs[1]:.4f}")
    print(f"  AE  AUC : {model_aucs[2]:.4f}")
    print(f"  Ensemble AUC : {ens_auc:.4f}  AP: {ens_ap:.4f}")
    print(f"  Best threshold: {best_thresh:.3f}")
    print(f"{'='*50}")

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_AnomalyDetection_Ensemble")
    with mlflow.start_run(run_name="Anomaly_train"):
        mlflow.log_param("contamination",   CONTAMINATION)
        mlflow.log_param("best_threshold",  round(best_thresh, 3))
        mlflow.log_metric("if_auc",         round(float(model_aucs[0]), 4))
        mlflow.log_metric("svm_auc",        round(float(model_aucs[1]), 4))
        mlflow.log_metric("ae_auc",         round(float(model_aucs[2]), 4))
        mlflow.log_metric("ensemble_auc",   round(ens_auc, 4))
        mlflow.log_metric("ensemble_ap",    round(ens_ap,  4))
        print("[train_anomaly_models] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":    "5G_AnomalyDetection_Ensemble",
            "run_name":      "Anomaly_train",
            "model":         "IsolationForest+SVM+PCA",
            "if_auc":        round(float(model_aucs[0]), 4),
            "svm_auc":       round(float(model_aucs[1]), 4),
            "ae_auc":        round(float(model_aucs[2]), 4),
            "ensemble_auc":  round(ens_auc, 4),
            "ensemble_ap":   round(ens_ap,  4),
            "best_threshold":round(best_thresh, 3),
            "type":          "training",
        })

    print("[train_anomaly_models] Done ✅\n")

    return {
        "models": {"if": best_if, "svm": best_oc, "ae": best_ae},
        "scaler": scaler_rob,
        "ensemble_scores": ens_tr,
        "test_scores": ens_te,
        "y_labels": y_labels,
        "best_threshold": best_thresh,
        "metrics": {
            "if_auc": model_aucs[0],
            "svm_auc": model_aucs[1],
            "ae_auc": model_aucs[2],
            "ens_auc": ens_auc,
            "ens_ap": ens_ap,
        },
    }


def evaluate_anomaly_models(
    ensemble_scores: np.ndarray,
    y_labels: pd.Series,
    best_threshold: float,
) -> dict:
    """
    Evaluate the anomaly detection ensemble and print metrics.

    Returns
    -------
    dict with auc, ap, f1, classification report
    """
    print("[evaluate_anomaly_models] Evaluating anomaly detection ensemble...")

    y_pred = (ensemble_scores >= best_threshold).astype(int)
    auc = roc_auc_score(y_labels, ensemble_scores)
    ap = average_precision_score(y_labels, ensemble_scores)
    f1 = f1_score(y_labels, y_pred)
    report = classification_report(y_labels, y_pred, target_names=["Normal", "Anomaly"])

    print(f"\n{'='*50}")
    print(f"  AUC-ROC           : {auc:.4f}")
    print(f"  Average Precision : {ap:.4f}")
    print(f"  F1 Score          : {f1:.4f}")
    print(f"  Threshold used    : {best_threshold:.3f}")
    print(f"{'='*50}")
    print("\nClassification Report:")
    print(report)

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_AnomalyDetection_Ensemble")
    with mlflow.start_run(run_name="Anomaly_evaluate"):
        mlflow.log_metric("val_auc_roc",          round(auc, 4))
        mlflow.log_metric("val_average_precision", round(ap,  4))
        mlflow.log_metric("val_f1_score",          round(f1,  4))
        mlflow.log_param("threshold_used",         round(best_threshold, 3))
        print("[evaluate_anomaly_models] MLflow run logged ✅")

    print("[evaluate_anomaly_models] Done ✅\n")

    return {"auc": auc, "ap": ap, "f1": f1, "report": report}


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — ONLINE LEARNING (Hoeffding Adaptive Tree)
# ═══════════════════════════════════════════════════════════════════════════════


def _make_online_features(row_vals: tuple) -> dict:
    """
    Convert a (Time, PLR, Delay, Category) tuple into a
    9-dimensional feature dict for the online model.
    """
    t, plr, delay, cat = row_vals
    return {
        "time_sin": float(np.sin(2 * np.pi * t / 24)),
        "time_cos": float(np.cos(2 * np.pi * t / 24)),
        "is_peak": float((8 <= t <= 10) or (18 <= t <= 21)),
        "log_plr": float(np.log10(max(plr, 1e-9))),
        "log_delay": float(np.log10(delay)),
        "plr_x_delay": float(np.log10(max(plr, 1e-9)) * np.log10(delay)),
        "lte5g_cat": float(cat),
        "high_delay": float(delay >= 150),
        "high_plr": float(plr >= 1e-2),
    }


def _build_online_labels(df: pd.DataFrame) -> pd.Series:
    """Build binary anomaly labels for the online learning stream."""
    y = pd.Series(0, index=df.index, dtype=int)
    y[(df["GBR"] == 1) & (df["Packet Loss Rate"] >= 1e-2)] = 1
    if "slice Type" in df.columns:
        y[
            (df["GBR"] == 1)
            & (df["Packet delay"] >= 150)
            & (df["slice Type"].isin([1, 2]))
        ] = 1
        y[(df["slice Type"] == 2) & (df["GBR"] == 0)] = 1
    return y


def train_online_model(
    train_raw: pd.DataFrame,
    random_state: int = RANDOM_STATE,
    window: int = 500,
    warmup: int = 200,
) -> dict:
    """
    Train a Hoeffding Adaptive Tree (HAT) classifier on the data stream.
    Includes:
        - Hyperparameter grid search
        - ADWIN drift detection on log_plr and log_delay
        - Rolling window metrics (accuracy, F1, AUC-ROC)

    Returns
    -------
    dict with:
        model        : trained HAT model
        scaler       : fitted river StandardScaler
        y_proba      : predicted probabilities on training stream
        y_labels     : true labels
        drift_log    : list of detected drift events
        metrics      : final AUC-ROC and Average Precision
    """
    print("[train_online_model] Preparing online learning stream...")

    y_labels = _build_online_labels(train_raw)
    X_raw = train_raw[BASE_FEATURES].values
    y_arr = y_labels.values
    WARMUP = warmup

    # ── Grid search ──────────────────────────────────────────────────────────
    print("[train_online_model] Running hyperparameter grid search...")
    param_grid = [
        {"grace_period": gp, "delta": d, "leaf_prediction": lp}
        for gp in [30, 50, 100]
        for d in [1e-4, 1e-5]
        for lp in ["nb", "nba"]
    ]

    best_auc, best_params = 0, param_grid[0]
    for params in param_grid:
        m = tree.HoeffdingAdaptiveTreeClassifier(
            grace_period=params["grace_period"],
            delta=params["delta"],
            leaf_prediction=params["leaf_prediction"],
            nb_threshold=30,
            seed=random_state,
        )
        sc = preprocessing.StandardScaler()
        pr = []
        for xv, yi in zip(X_raw, y_arr):
            x = _make_online_features(xv)
            sc.learn_one(x)
            xs = sc.transform_one(x)
            pr.append(m.predict_proba_one(xs).get(1, 0.0))
            m.learn_one(xs, yi)
        auc = roc_auc_score(y_arr[WARMUP:], pr[WARMUP:])
        if auc > best_auc:
            best_auc = auc
            best_params = params

    print(f"[train_online_model] Best params: {best_params} | AUC: {best_auc:.4f}")

    # ── Final training run with best params ──────────────────────────────────
    print("[train_online_model] Training final HAT model...")
    model = tree.HoeffdingAdaptiveTreeClassifier(
        grace_period=int(best_params["grace_period"]),
        delta=float(best_params["delta"]),
        leaf_prediction=str(best_params["leaf_prediction"]),
        nb_threshold=30,
        seed=random_state,
    )
    scaler_online = preprocessing.StandardScaler()

    adwin_plr = drift.ADWIN(delta=0.002)
    adwin_delay = drift.ADWIN(delta=0.002)

    roll_acc = Rolling(metrics.Accuracy(), window_size=window)
    roll_f1 = Rolling(metrics.F1(), window_size=window)

    y_proba, y_pred_list = [], []
    drift_log = []

    for i, (xv, yi) in enumerate(zip(X_raw, y_arr)):
        x = _make_online_features(xv)
        scaler_online.learn_one(x)
        xs = scaler_online.transform_one(x)

        prob = model.predict_proba_one(xs)
        p1 = prob.get(1, 0.0)
        pred = model.predict_one(xs)
        safe_pred = pred if pred is not None else 0

        y_proba.append(p1)
        y_pred_list.append(safe_pred)

        roll_acc.update(yi, safe_pred)
        roll_f1.update(yi, safe_pred)

        adwin_plr.update(x["log_plr"])
        adwin_delay.update(x["log_delay"])
        if adwin_plr.drift_detected:
            drift_log.append({"sample": i, "signal": "log_plr"})
        if adwin_delay.drift_detected:
            drift_log.append({"sample": i, "signal": "log_delay"})

        model.learn_one(xs, yi)

    auc_final = roc_auc_score(y_arr[WARMUP:], y_proba[WARMUP:])
    ap_final = average_precision_score(y_arr[WARMUP:], y_proba[WARMUP:])

    print(f"\n{'='*50}")
    print(f"  AUC-ROC          : {auc_final:.4f}")
    print(f"  Average Precision: {ap_final:.4f}")
    print(f"  Rolling Accuracy : {roll_acc.get():.4f} (last {window} samples)")
    print(f"  Rolling F1       : {roll_f1.get():.4f} (last {window} samples)")
    print(f"  Drift events     : {len(drift_log)}")
    print(f"{'='*50}")

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_OnlineLearning_HAT")
    with mlflow.start_run(run_name="HAT_train"):
        mlflow.log_param("grace_period",    best_params["grace_period"])
        mlflow.log_param("delta",           best_params["delta"])
        mlflow.log_param("leaf_prediction", best_params["leaf_prediction"])
        mlflow.log_param("n_batches",       window)
        mlflow.log_param("warmup",          WARMUP)
        mlflow.log_metric("auc_roc",        round(auc_final,      4))
        mlflow.log_metric("average_precision", round(ap_final,    4))
        mlflow.log_metric("rolling_accuracy",  round(roll_acc.get(), 4))
        mlflow.log_metric("rolling_f1",        round(roll_f1.get(),  4))
        mlflow.log_metric("drift_events",      len(drift_log))
        print("[train_online_model] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":       "5G_OnlineLearning_HAT",
            "run_name":         "HAT_train",
            "model":            "HoeffdingAdaptiveTree",
            "auc_roc":          round(auc_final,       4),
            "average_precision":round(ap_final,        4),
            "rolling_accuracy": round(roll_acc.get(),  4),
            "rolling_f1":       round(roll_f1.get(),   4),
            "drift_events":     len(drift_log),
            "type":             "training",
        })

    print("[train_online_model] Done ✅\n")

    return {
        "model": model,
        "scaler": scaler_online,
        "y_proba": y_proba,
        "y_labels": y_arr,
        "drift_log": drift_log,
        "metrics": {"auc": auc_final, "ap": ap_final},
    }


def evaluate_online_model(
    model,
    scaler,
    test_raw: pd.DataFrame,
) -> dict:
    """
    Evaluate the trained HAT model on the test stream.

    Returns
    -------
    dict with auc, ap, classification report
    """
    print("[evaluate_online_model] Evaluating HAT on test stream...")

    y_test = _build_online_labels(test_raw)
    X_test = test_raw[BASE_FEATURES].values
    y_arr = y_test.values

    y_proba, y_pred = [], []
    for xv in X_test:
        x = _make_online_features(xv)
        xs = scaler.transform_one(x)
        p1 = model.predict_proba_one(xs).get(1, 0.0)
        pred = model.predict_one(xs)
        y_proba.append(p1)
        y_pred.append(pred if pred is not None else 0)

    auc = roc_auc_score(y_arr, y_proba)
    ap = average_precision_score(y_arr, y_proba)
    report = classification_report(y_arr, y_pred, target_names=["Normal", "Anomaly"])

    print(f"\n{'='*50}")
    print(f"  AUC-ROC          : {auc:.4f}")
    print(f"  Average Precision: {ap:.4f}")
    print(f"{'='*50}")
    print("\nClassification Report:")
    print(report)

    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_OnlineLearning_HAT")
    with mlflow.start_run(run_name="HAT_evaluate"):
        mlflow.log_metric("test_auc_roc",          round(auc, 4))
        mlflow.log_metric("test_average_precision", round(ap,  4))
        print("[evaluate_online_model] MLflow run logged ✅")

    print("[evaluate_online_model] Done ✅\n")

    return {"auc": auc, "ap": ap, "report": report}
# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — XAI (SHAP + LIME Explainability)
# ═══════════════════════════════════════════════════════════════════════════════

def explain_model(
    model: RandomForestClassifier,
    X_val: np.ndarray,
    feature_names: list = None,
    n_samples: int = 200,
    lime_index: int = 0,
) -> dict:
    """
    Generate SHAP and LIME explanations for the Random Forest model.
    Logs explainability metrics and artifacts to MLflow.

    Parameters
    ----------
    model         : fitted RandomForestClassifier
    X_val         : validation feature array
    feature_names : list of feature names (default: FEAT_NAMES)
    n_samples     : number of samples to use for SHAP (default: 200)
    lime_index    : index of the sample to explain with LIME (default: 0)

    Returns
    -------
    dict with keys:
        shap_values       : SHAP values array
        shap_importance   : mean absolute SHAP per feature
        lime_explanation  : LIME explanation object
        top_shap_feature  : most important feature by SHAP
        top_lime_feature  : most important feature by LIME
    """
    import shap
    import lime
    import lime.lime_tabular

    if feature_names is None:
        feature_names = FEAT_NAMES

    print("[explain_model] Computing SHAP values...")
    sample_size = min(n_samples, len(X_val))
    X_sample    = X_val[:sample_size]

    # ── SHAP ─────────────────────────────────────────────────────────────────
    explainer   = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)

    # shap_values can be:
    #   - a list of 2D arrays (one per class) for multi-class RF
    #   - a single 3D array of shape (n_samples, n_features, n_classes)
    #   - a single 2D array of shape (n_samples, n_features)
    if isinstance(shap_values, list):
        # list of arrays, one per class → average absolute SHAP across classes
        mean_abs_shap = np.mean(
            [np.abs(sv).mean(axis=0) for sv in shap_values],
            axis=0,
        )
    elif shap_values.ndim == 3:
        # 3D array (n_samples, n_features, n_classes)
        mean_abs_shap = np.abs(shap_values).mean(axis=(0, 2))
    else:
        # 2D array (n_samples, n_features)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)

    # Safety check: align length with feature_names
    mean_abs_shap = mean_abs_shap[:len(feature_names)]

    shap_importance = {
        feature_names[i]: round(float(mean_abs_shap[i]), 6)
        for i in range(len(feature_names))
    }
    top_shap_feature = max(shap_importance, key=shap_importance.get)

    print(f"[explain_model] Top SHAP feature: {top_shap_feature} "
          f"({shap_importance[top_shap_feature]:.4f})")

    # ── LIME ─────────────────────────────────────────────────────────────────
    print("[explain_model] Computing LIME explanation...")
    lime_explainer = lime.lime_tabular.LimeTabularExplainer(
        training_data  = X_val,
        feature_names  = feature_names,
        class_names    = [SLICE_NAMES[k] for k in sorted(SLICE_NAMES)],
        mode           = "classification",
        random_state   = RANDOM_STATE,
    )

    lime_exp = lime_explainer.explain_instance(
        data_row       = X_val[lime_index],
        predict_fn     = model.predict_proba,
        num_features   = len(feature_names),
    )

    lime_weights = dict(lime_exp.as_list())
    top_lime_feature = max(lime_weights, key=lambda k: abs(lime_weights[k]),
                           default=feature_names[0])

    print(f"[explain_model] Top LIME feature : {top_lime_feature}")

    # ── MLflow logging ────────────────────────────────────────────────────────
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:////home/emna/network_slicing_pipeline/mlflow.db"))
    mlflow.set_experiment("5G_XAI_Explainability")

    with mlflow.start_run(run_name="XAI_SHAP_LIME"):
        # Log SHAP importance scores as metrics
        for feat, val in shap_importance.items():
            mlflow.log_metric(f"shap_{feat}", val)

        # Log top features as params
        mlflow.log_param("top_shap_feature",  top_shap_feature)
        mlflow.log_param("top_lime_feature",  top_lime_feature)
        mlflow.log_param("shap_sample_size",  sample_size)
        mlflow.log_param("lime_sample_index", lime_index)
        mlflow.log_param("n_features",        len(feature_names))

        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":      "5G_XAI_Explainability",
            "run_name":        "XAI_SHAP_LIME",
            "model":           "RandomForest_SHAP_LIME",
            "top_shap_feature":top_shap_feature,
            "top_lime_feature":top_lime_feature,
            "shap_scores":     shap_importance,
            "type":            "explainability",
        })
        # Save SHAP importance as a CSV artifact
        import tempfile
        shap_df = pd.DataFrame(
            list(shap_importance.items()),
            columns=["feature", "mean_abs_shap"]
        ).sort_values("mean_abs_shap", ascending=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            shap_path = os.path.join(tmpdir, "shap_importance.csv")
            shap_df.to_csv(shap_path, index=False)
            mlflow.log_artifact(shap_path)

        print("[explain_model] MLflow XAI run logged ✅")

    print("\n📊 SHAP Feature Importance:")
    print("=" * 40)
    for feat, val in sorted(shap_importance.items(),
                            key=lambda x: x[1], reverse=True):
        print(f"  {feat:<20} : {val:.6f}")

    print(f"\n📊 Top LIME weights (sample {lime_index}):")
    print("=" * 40)
    for feat, val in sorted(lime_weights.items(),
                            key=lambda x: abs(x[1]), reverse=True):
        print(f"  {feat:<30} : {val:+.6f}")

    print("[explain_model] Done ✅\n")

    return {
        "shap_values"     : shap_values,
        "shap_importance" : shap_importance,
        "lime_explanation": lime_exp,
        "top_shap_feature": top_shap_feature,
        "top_lime_feature": top_lime_feature,
    }

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — MODEL I/O
# ═══════════════════════════════════════════════════════════════════════════════


def save_model(
    model,
    scaler,
    model_path: str = "model.pkl",
    scaler_path: str = "scaler.pkl",
) -> None:
    """Save a model and its scaler to disk using joblib."""
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    print(f"[save_model] Model  saved → {model_path} ✅")
    print(f"[save_model] Scaler saved → {scaler_path} ✅\n")


def load_model(
    model_path: str = "model.pkl",
    scaler_path: str = "scaler.pkl",
) -> tuple:
    """Load a saved model and scaler from disk."""
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    print(f"[load_model] Model  loaded ← {model_path}  ✅")
    print(f"[load_model] Scaler loaded ← {scaler_path} ✅\n")
    return model, scaler
