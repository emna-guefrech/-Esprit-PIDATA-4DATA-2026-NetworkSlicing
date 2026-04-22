"""
model_pipeline.py
=================
Modularised ML pipeline for 6G Network Slicing.

DSOs covered:
  - prepare_data()          : load & clean network_slicing_dataset - v3_6G_OLD.csv
  - DSO1  : train_model_regression()   / evaluate_model_regression()
  - DSO5.2: train_model_anomaly()      / evaluate_model_anomaly()
  - DSO5.3: train_model_online()       / evaluate_model_online()
  - DSO5.4: train_model_xai()          / evaluate_model_xai()
  - save_model() / load_model()
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import time
import mlflow
import mlflow.sklearn
import mlflow.xgboost

from datetime import datetime, timezone
from elasticsearch import Elasticsearch

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
        doc["pipeline"]   = "6G"
        es.index(index=index, document=doc)
    except Exception as e:
        print(f"[ES] Failed to log: {e}")

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (
    r2_score,
    mean_squared_error,
    mean_absolute_error,
    accuracy_score,
    f1_score,
    classification_report,
)
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import SGDClassifier
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# SHARED UTILITY
# ─────────────────────────────────────────────


def safe_sigmoid(x):
    """Numerically stable sigmoid."""
    x = np.clip(x, -10, 10)
    return 1 / (1 + np.exp(-x))


# ─────────────────────────────────────────────
# 1. prepare_data()
# ─────────────────────────────────────────────


def prepare_data(raw_path="network_slicing_dataset - v3_6G_OLD.csv", output_path="network_slicing_dataset_final.csv"):
    """
    Load, clean, impute and save the raw 6G dataset.

    Steps:
      - Load CSV (semicolon-separated)
      - Convert budget columns (comma decimal → float)
      - Impute zero values with per-column median
      - Convert time units ns → μs
      - Remove bias column 'Use Case Type'
      - Save cleaned CSV

    Parameters
    ----------
    raw_path   : path to the raw CSV file
    output_path: path where the cleaned CSV will be saved

    Returns
    -------
    df_clean : pandas DataFrame
    """
    print("📥 Loading raw dataset...")
    df = pd.read_csv(raw_path, sep=";")
    print(f"   Shape: {df.shape}")

    # Fix decimal separator on budget columns
    budget_columns = ["Packet Loss Budget", "Latency Budget (ns)", "Jitter Budget (ns)", "Data R date Budget (Gbps)"]
    for col in budget_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", ".").astype(float)

    # ── Imputation: replace zeros with non-zero median ────────────
    imputation_columns = ["Latency Budget (ns)", "Jitter Budget (ns)", "Data R date Budget (Gbps)"]
    df_imputed = df.copy()
    print("\n🔧 Imputing zero values...")
    for col in imputation_columns:
        if col not in df_imputed.columns:
            continue
        median_val = df_imputed[df_imputed[col] > 0][col].median()
        zero_mask = df_imputed[col] == 0
        df_imputed.loc[zero_mask, col] = median_val
        print(f"   {col}: {zero_mask.sum()} zeros → median {median_val:.2f}")

    # ── Unit conversion: ns → μs ──────────────────────────────────
    print("\n🔄 Converting ns → μs...")
    time_cols = [c for c in df_imputed.columns if "(ns)" in c]
    for col in time_cols:
        df_imputed[col] = df_imputed[col] / 1000
        new_name = col.replace("(ns)", "(μs)")
        df_imputed.rename(columns={col: new_name}, inplace=True)
        print(f"   {col} → {new_name}")

    # ── Remove bias column ────────────────────────────────────────
    df_clean = df_imputed.copy()
    if "Use Case Type" in df_clean.columns:
        df_clean.drop("Use Case Type", axis=1, inplace=True)
        print("\n🚫 'Use Case Type' removed (bias column)")

    # ── Save ──────────────────────────────────────────────────────
    df_clean.to_csv(output_path, index=False, sep=";")
    print(f"\n💾 Clean dataset saved → {output_path}")
    print(f"   Final shape: {df_clean.shape}")
    return df_clean


# ─────────────────────────────────────────────
# 2. DSO 1 — QoS Probability Regression
# ─────────────────────────────────────────────


def train_model_regression(dataset_path="network_slicing_congestion_final.csv"):
    """
    DSO 1 — Train regression models to predict QoS_Probability.

    Models: RandomForestRegressor, XGBRegressor (+ GridSearchCV tuning).

    Parameters
    ----------
    dataset_path : path to the congestion CSV

    Returns
    -------
    dict with keys: best_model, best_name, scaler (None), features,
                    X_test, y_test, results
    """
    print("=" * 55)
    print("DSO 1 — QoS PROBABILITY REGRESSION")
    print("=" * 55)

    df = pd.read_csv(dataset_path, encoding="utf-8")
    epsilon = 1e-9

    # Build gap features
    df["Latency_Gap"] = df["Latency Budget (μs)"] - df["Slice Latency (μs)"]
    df["Packet_Loss_Gap"] = df["Packet Loss Budget"] - df["Slice Packet Loss"]
    df["Jitter_Gap"] = df["Jitter Budget (μs)"] - df["Slice Jitter (μs)"]
    df["Rate_Gap"] = df["Slice Available Transfer Rate (Gbps)"] - df["Data Rate Budget (Gbps)"]

    # Build target: QoS_Probability via sigmoid-normalised scores
    df["Latency_Score"] = safe_sigmoid(df["Latency_Gap"] / (df["Latency Budget (μs)"] + epsilon))
    df["Packet_Loss_Score"] = safe_sigmoid(df["Packet_Loss_Gap"] / (df["Packet Loss Budget"] + epsilon))
    df["Jitter_Score"] = safe_sigmoid(df["Jitter_Gap"] / (df["Jitter Budget (μs)"] + epsilon))
    df["Rate_Score"] = safe_sigmoid(df["Rate_Gap"] / (df["Data Rate Budget (Gbps)"] + epsilon))

    df["QoS_Probability"] = (df["Latency_Score"] + df["Packet_Loss_Score"] + df["Jitter_Score"] + df["Rate_Score"]) / 4
    df["QoS_Probability"] = df["QoS_Probability"].clip(0, 1).fillna(0)

    feature_cols = ["Latency_Gap", "Packet_Loss_Gap", "Jitter_Gap", "Rate_Gap"]
    X = df[feature_cols]
    y = df["QoS_Probability"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train: {X_train.shape}  Test: {X_test.shape}")

    # ── Train base models ─────────────────────────────────────────
    models = {
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "XGBoost": XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
    }
    results = {}
    mlflow.set_tracking_uri("sqlite:////home/emna/network_slicing_pipeline/mlflow.db")
    mlflow.set_experiment("6G_DSO1_QoS_Regression")

    for name, model in models.items():
        print(f"\n🚀 Training {name}...")
        t0 = time.time()
        model.fit(X_train, y_train)
        t_train = time.time() - t0
        y_pred = model.predict(X_test)
        r2   = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae  = mean_absolute_error(y_test, y_pred)
        results[name] = {'R2': r2, 'RMSE': rmse, 'MAE': mae,
                         'TrainTime': round(t_train, 4),
                         'y_pred': y_pred, 'model': model}
        print(f"   R²={r2:.4f} | RMSE={rmse:.4f} | MAE={mae:.4f} | {t_train:.2f}s")

        with mlflow.start_run(run_name=f"DSO1_{name}"):
            mlflow.log_param("model_name",   name)
            mlflow.log_param("train_size",   X_train.shape[0])
            mlflow.log_param("n_features",   X_train.shape[1])
            mlflow.log_metric("r2_score",    round(r2, 4))
            mlflow.log_metric("rmse",        round(rmse, 4))
            mlflow.log_metric("mae",         round(mae, 4))
            mlflow.log_metric("train_time",  round(t_train, 4))
            if hasattr(model, "get_booster"):
                mlflow.xgboost.log_model(model, artifact_path=f"{name}_model")
            else:
                mlflow.sklearn.log_model(model, artifact_path=f"{name}_model")
            print(f"   MLflow run logged for {name} ✅")
            
            # Log to Elasticsearch
            _log_to_es("mlflow-metrics", {
                "experiment": "6G_DSO1_QoS_Regression",
                "run_name":   f"DSO1_{name}",
                "model":      name,
                "r2_score":   round(r2,   4),
                "rmse":       round(rmse, 4),
                "mae":        round(mae,  4),
                "train_time": round(t_train, 4),
                "type":       "training",
            })
    # ── GridSearchCV on XGBoost ───────────────────────────────────
    print("\n🔍 Tuning XGBoost with GridSearchCV...")
    params = {
        "n_estimators": [100, 300],
        "max_depth": [3, 5, 7],
        "learning_rate": [0.05, 0.1],
    }
    grid = GridSearchCV(
        XGBRegressor(random_state=42, verbosity=0),
        params,
        cv=5,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
        verbose=0,
    )
    grid.fit(X_train, y_train)
    print(f"   Best params : {grid.best_params_}")
    print(f"   Best RMSE   : {-grid.best_score_:.4f}")

    best_xgb = grid.best_estimator_
    y_pred_tuned = best_xgb.predict(X_test)
    r2_tuned = r2_score(y_test, y_pred_tuned)
    rmse_tuned = np.sqrt(mean_squared_error(y_test, y_pred_tuned))
    results["XGBoost_Tuned"] = {
        "R2": r2_tuned,
        "RMSE": rmse_tuned,
        "MAE": mean_absolute_error(y_test, y_pred_tuned),
        "y_pred": y_pred_tuned,
        "model": best_xgb,
    }
    print(f"   Tuned XGBoost — R²={r2_tuned:.4f} | RMSE={rmse_tuned:.4f}")

    # Pick best
    best_name = max(results, key=lambda k: results[k]["R2"])
    best_model = results[best_name]["model"]
    print(f"\n🏆 Best model: {best_name} (R²={results[best_name]['R2']:.4f})")

    return {
        "best_model": best_model,
        "best_name": best_name,
        "features": feature_cols,
        "X_test": X_test,
        "y_test": y_test,
        "results": results,
    }


def evaluate_model_regression(train_output):
    """
    DSO 1 — Print comparison table and plot predicted vs actual.

    Parameters
    ----------
    train_output : dict returned by train_model_regression()
    """
    results = train_output["results"]
    best_name = train_output["best_name"]
    y_test = train_output["y_test"]

    # Comparison table
    rows = {n: {k: v for k, v in r.items() if k not in ("y_pred", "model")} for n, r in results.items()}
    df_cmp = pd.DataFrame(rows).T
    print("\n📊 Model Comparison — DSO 1 Regression")
    print("=" * 55)
    print(df_cmp.round(4).to_string())

    # Plot best model
    y_pred = results[best_name]["y_pred"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    axes[0].scatter(y_test, y_pred, alpha=0.3, s=10, color="steelblue")
    axes[0].plot([0, 1], [0, 1], "r--", linewidth=1.5, label="Perfect prediction")
    axes[0].set_xlabel("Actual QoS_Probability")
    axes[0].set_ylabel("Predicted QoS_Probability")
    axes[0].set_title(f"Predicted vs Actual — {best_name}")
    axes[0].legend()

    residuals = y_test.values - y_pred
    axes[1].hist(residuals, bins=50, color="coral", alpha=0.85, edgecolor="white")
    axes[1].axvline(0, color="red", linestyle="--")
    axes[1].set_xlabel("Residual (actual − predicted)")
    axes[1].set_ylabel("Frequency")
    axes[1].set_title("Residual Distribution")

    plt.suptitle("DSO 1 — QoS Probability Regression Evaluation", fontweight="bold")
    plt.tight_layout()
    plt.savefig("eval_dso1_regression.png", dpi=120, bbox_inches="tight")
    plt.show()
    print("📊 Plot saved → eval_dso1_regression.png")


# ─────────────────────────────────────────────
# 3. DSO 5.2 — Anomaly Detection (Isolation Forest)
# ─────────────────────────────────────────────


def train_model_anomaly(dataset_path="network_slicing_congestion_final.csv"):
    """
    DSO 5.2 — Train Isolation Forest for anomaly detection.

    Parameters
    ----------
    dataset_path : path to the congestion CSV

    Returns
    -------
    dict with keys: model, scaler, features, df_result
    """
    print("=" * 55)
    print("DSO 5.2 — ANOMALY DETECTION (Isolation Forest)")
    print("=" * 55)

    df = pd.read_csv(dataset_path, encoding="utf-8")
    df.columns = df.columns.str.strip()

    features_anomaly = [
        "Slice Latency (μs)",
        "Slice Packet Loss",
        "Slice Jitter (μs)",
        "Slice Available Transfer Rate (Gbps)",
        "Latency_Stress_Ratio",
        "Bandwidth_Usage_Ratio",
        "Mobility_Jitter_Impact",
        "Required Mobility",
        "Required Connectivity",
    ]
    features_valides = [c for c in features_anomaly if c in df.columns]
    print(f"✅ Valid features ({len(features_valides)}/{len(features_anomaly)}): {features_valides}")

    df_model = df[features_valides].dropna().copy()
    print(f"   Dataset shape: {df_model.shape}")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_model)

    print("\n🚀 Training Isolation Forest...")
    iso_forest = IsolationForest(contamination=0.05, random_state=42)
    iso_forest.fit(X_scaled)

    df_model["anomaly"] = iso_forest.predict(X_scaled)
    df_model["anomaly_score"] = iso_forest.score_samples(X_scaled)

    anomaly_rate = (df_model['anomaly'] == -1).mean() * 100
    print(f"\nDistribution:  1=Normal | -1=Anomaly")
    print(df_model['anomaly'].value_counts().to_string())
    print(f"Anomaly rate: {anomaly_rate:.1f}%")

    import mlflow
    mlflow.set_tracking_uri("sqlite:////home/emna/network_slicing_pipeline/mlflow.db")
    mlflow.set_experiment("6G_DSO52_AnomalyDetection")
    with mlflow.start_run(run_name="DSO52_IsolationForest"):
        mlflow.log_param("contamination", 0.05)
        mlflow.log_param("train_size",    len(df_model))
        mlflow.log_metric("anomaly_rate", round(anomaly_rate / 100, 4))
        mlflow.sklearn.log_model(iso_forest, artifact_path="isolation_forest")
        print("[train_model_anomaly] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":  "6G_DSO52_AnomalyDetection",
            "run_name":    "DSO52_IsolationForest",
            "model":       "IsolationForest",
            "anomaly_rate":round(anomaly_rate / 100, 4),
            "type":        "training",
        })

    return {
        "model": iso_forest,
        "scaler": scaler,
        "features": features_valides,
        "df_result": df_model,
    }


def evaluate_model_anomaly(train_output):
    """
    DSO 5.2 — Plot anomaly score distribution.

    Parameters
    ----------
    train_output : dict returned by train_model_anomaly()
    """
    df_model = train_output["df_result"]

    plt.figure(figsize=(10, 4))
    plt.hist(
        df_model[df_model["anomaly"] == 1]["anomaly_score"],
        bins=50,
        alpha=0.7,
        color="steelblue",
        label="Normal",
        edgecolor="white",
    )
    plt.hist(
        df_model[df_model["anomaly"] == -1]["anomaly_score"],
        bins=50,
        alpha=0.7,
        color="red",
        label="Anomaly",
        edgecolor="white",
    )
    plt.xlabel("Anomaly Score")
    plt.ylabel("Frequency")
    plt.title("DSO 5.2 — Isolation Forest: Anomaly Score Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig("eval_dso52_anomaly.png", dpi=120, bbox_inches="tight")
    plt.show()
    print("📊 Plot saved → eval_dso52_anomaly.png")
    print(f"\nAnomalies  : {(df_model['anomaly'] == -1).sum()}")
    print(f"Normal     : {(df_model['anomaly'] == 1).sum()}")


# ─────────────────────────────────────────────
# 4. DSO 5.3 — Online Learning (SGDClassifier)
# ─────────────────────────────────────────────


def train_model_online(dataset_path="network_slicing_congestion_final.csv", n_batches=10):
    """
    DSO 5.3 — Incremental (online) learning with SGDClassifier.

    Parameters
    ----------
    dataset_path : path to the congestion CSV
    n_batches    : number of training batches

    Returns
    -------
    dict with keys: model, scaler, encoder, features,
                    X_test, y_test, history, le
    """
    print("=" * 55)
    print("DSO 5.3 — ONLINE LEARNING (SGDClassifier)")
    print("=" * 55)

    df = pd.read_csv(dataset_path, encoding="utf-8")

    exclude_cols = [
        "congestion_class",
        "Latency_Gap",
        "Packet_Loss_Gap",
        "Jitter_Gap",
        "Rate_Gap",
        "Latency_Score",
        "Packet_Loss_Score",
        "Jitter_Score",
        "Rate_Score",
        "QoS_Probability",
        "Efficiency_Index",
        "Aggregated_QoS_Score",
        "SLA_Respected",
    ]
    target_col = "congestion_class"
    feature_cols = [c for c in df.columns if c not in exclude_cols and c != target_col]

    le = LabelEncoder()
    df["target_enc"] = le.fit_transform(df[target_col].astype(str))

    X = df[feature_cols].select_dtypes(include=[np.number])
    y = df.loc[X.index, "target_enc"]

    # Remove rare class (class '2' with only 1 sample)
    if "2" in le.classes_:
        rare_label = le.transform(["2"])[0]
        mask = y != rare_label
        X = X[mask].reset_index(drop=True)
        y = y[mask].reset_index(drop=True)

    print(f"Features: {X.shape[1]}  |  Classes: {pd.Series(le.inverse_transform(y)).value_counts().to_dict()}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)

    # Simulate batches
    batch_size = len(X_train_sc) // n_batches
    batches_X = [X_train_sc[i * batch_size : (i + 1) * batch_size] for i in range(n_batches)]
    batches_y = [y_train.values[i * batch_size : (i + 1) * batch_size] for i in range(n_batches)]
    print(f"📦 {n_batches} batches of ~{batch_size} samples each")

    classes_all = np.unique(y)
    sgd = SGDClassifier(loss="modified_huber", max_iter=1, random_state=42, n_jobs=-1)

    history = []
    print("\n" + "=" * 55)
    print("INCREMENTAL TRAINING")
    print("=" * 55)
    for i, (bX, by) in enumerate(zip(batches_X, batches_y)):
        sgd.partial_fit(bX, by, classes=classes_all)
        y_pred_b = sgd.predict(X_test_sc)
        acc = accuracy_score(y_test, y_pred_b)
        f1 = f1_score(y_test, y_pred_b, average="weighted", zero_division=0)
        history.append({"batch": i + 1, "accuracy": acc, "f1": f1})
        print(f"  Batch {i+1:2d}/{n_batches} | Accuracy: {acc:.4f} | F1: {f1:.4f}")

    print(f"\n✅ Final — Accuracy: {history[-1]['accuracy']:.4f} | F1: {history[-1]['f1']:.4f}")

    import mlflow
    mlflow.set_tracking_uri("sqlite:////home/emna/network_slicing_pipeline/mlflow.db")
    mlflow.set_experiment("6G_DSO53_OnlineLearning")
    with mlflow.start_run(run_name="DSO53_SGD_Online"):
        mlflow.log_param("n_batches",       n_batches)
        mlflow.log_param("train_size",      len(X_train))
        mlflow.log_metric("final_accuracy", round(history[-1]['accuracy'], 4))
        mlflow.log_metric("final_f1",       round(history[-1]['f1'],       4))
        print("[train_model_online] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment":     "6G_DSO53_OnlineLearning",
            "run_name":       "DSO53_SGD_Online",
            "model":          "SGDClassifier",
            "final_accuracy": round(history[-1]['accuracy'], 4),
            "final_f1":       round(history[-1]['f1'],       4),
            "n_batches":      n_batches,
            "type":           "training",
        })
    return {
        "model": sgd,
        "scaler": scaler,
        "encoder": le,
        "features": X.columns.tolist(),
        "X_test": X_test_sc,
        "y_test": y_test,
        "history": history,
        "le": le,
    }


def evaluate_model_online(train_output):
    """
    DSO 5.3 — Plot accuracy/F1 convergence and print classification report.

    Parameters
    ----------
    train_output : dict returned by train_model_online()
    """
    history = train_output["history"]
    model = train_output["model"]
    X_test = train_output["X_test"]
    y_test = train_output["y_test"]
    le = train_output["le"]

    df_h = pd.DataFrame(history)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(df_h["batch"], df_h["accuracy"], marker="o", color="steelblue", linewidth=2)
    ax1.fill_between(df_h["batch"], df_h["accuracy"], alpha=0.15, color="steelblue")
    ax1.set_title("Accuracy per batch", fontweight="bold")
    ax1.set_xlabel("Batch")
    ax1.set_ylabel("Accuracy")
    ax1.set_ylim(0, 1.05)
    ax1.grid(True, alpha=0.3)

    ax2.plot(df_h["batch"], df_h["f1"], marker="s", color="coral", linewidth=2)
    ax2.fill_between(df_h["batch"], df_h["f1"], alpha=0.15, color="coral")
    ax2.set_title("F1-Score (weighted) per batch", fontweight="bold")
    ax2.set_xlabel("Batch")
    ax2.set_ylabel("F1-Score")
    ax2.set_ylim(0, 1.05)
    ax2.grid(True, alpha=0.3)

    plt.suptitle("DSO 5.3 — Online Learning Convergence", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig("eval_dso53_online.png", dpi=120, bbox_inches="tight")
    plt.show()
    print("📊 Plot saved → eval_dso53_online.png")

    y_pred_final = model.predict(X_test)
    present_cls = sorted(set(y_test) | set(y_pred_final))
    present_names = le.inverse_transform(present_cls)
    print("\n📋 Classification Report — SGDClassifier")
    print("=" * 55)
    print(classification_report(y_test, y_pred_final, labels=present_cls, target_names=present_names, zero_division=0))


# ─────────────────────────────────────────────
# 5. DSO 5.4 — XAI Dashboard (SHAP + XGBoost)
# ─────────────────────────────────────────────


def train_model_xai(dataset_path="network_slicing_congestion_final.csv"):
    """
    DSO 5.4 — Train XGBoost for QoS_Probability and compute SHAP values.

    Parameters
    ----------
    dataset_path : path to the congestion CSV

    Returns
    -------
    dict with keys: model, explainer, shap_values, X_sample,
                    feature_names, y_pred_sample, expected_value,
                    idx_high, idx_low
    """
    try:
        import shap
    except ImportError:
        import subprocess, sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "shap", "-q"])
        import shap

    print("=" * 55)
    print("DSO 5.4 — XAI DASHBOARD (SHAP + XGBoost)")
    print("=" * 55)

    df = pd.read_csv(dataset_path, encoding="utf-8")
    epsilon = 1e-9

    df["Latency_Gap"] = df["Latency Budget (μs)"] - df["Slice Latency (μs)"]
    df["Packet_Loss_Gap"] = df["Packet Loss Budget"] - df["Slice Packet Loss"]
    df["Jitter_Gap"] = df["Jitter Budget (μs)"] - df["Slice Jitter (μs)"]
    df["Rate_Gap"] = df["Slice Available Transfer Rate (Gbps)"] - df["Data Rate Budget (Gbps)"]

    norm_lat = df["Latency_Gap"] / (df["Latency Budget (μs)"] + epsilon)
    norm_pkt = df["Packet_Loss_Gap"] / (df["Packet Loss Budget"] + epsilon)
    norm_jit = df["Jitter_Gap"] / (df["Jitter Budget (μs)"] + epsilon)
    norm_rate = df["Rate_Gap"] / (df["Slice Available Transfer Rate (Gbps)"] + epsilon)

    raw_score = 0.35 * norm_lat + 0.30 * norm_pkt + 0.20 * norm_jit + 0.15 * norm_rate
    df["QoS_Probability"] = safe_sigmoid(raw_score * 3)

    feature_names = ["Latency_Gap", "Packet_Loss_Gap", "Jitter_Gap", "Rate_Gap"]
    X = df[feature_names]
    y = df["QoS_Probability"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("🚀 Training XGBoost (tuned)...")
    xgb = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.1, random_state=42, verbosity=0)
    xgb.fit(X_train, y_train)

    y_pred = xgb.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"✅ XGBoost — R²: {r2:.4f} | RMSE: {rmse:.4f}")
    print(f"   Dataset shape : {X_train.shape}")

    import mlflow
    import mlflow.xgboost
    mlflow.set_tracking_uri("sqlite:////home/emna/network_slicing_pipeline/mlflow.db")
    mlflow.set_experiment("6G_DSO54_XAI_XGBoost")
    with mlflow.start_run(run_name="DSO54_XGBoost_XAI"):
        mlflow.log_param("n_estimators",  300)
        mlflow.log_param("max_depth",     5)
        mlflow.log_param("learning_rate", 0.1)
        mlflow.log_metric("r2_score",     round(r2,   4))
        mlflow.log_metric("rmse",         round(rmse, 4))
        mlflow.xgboost.log_model(xgb, artifact_path="xgboost_xai_model")
        print("[train_model_xai] MLflow run logged ✅")
        
        # Log to Elasticsearch
        _log_to_es("mlflow-metrics", {
            "experiment": "6G_DSO54_XAI_XGBoost",
            "run_name":   "DSO54_XGBoost_XAI",
            "model":      "XGBoost_XAI",
            "r2_score":   round(r2,   4),
            "rmse":       round(rmse, 4),
            "type":       "training",
        })

    # SHAP
    print("\n🔍 Computing SHAP values (sample=500)...")
    explainer = shap.TreeExplainer(xgb)
    sample_size = min(500, len(X_test))
    X_sample = X_test.iloc[:sample_size].reset_index(drop=True)
    shap_values = explainer.shap_values(X_sample)
    expected_v = explainer.expected_value

    print(f"   Expected value (baseline): {expected_v:.4f}")
    mean_abs = pd.Series(np.abs(shap_values).mean(axis=0), index=feature_names).sort_values(ascending=False)
    print("\n📊 Mean |SHAP| per feature:")
    print(mean_abs.round(4).to_string())

    y_pred_sample = xgb.predict(X_sample)
    idx_high = int(np.argmax(y_pred_sample))
    idx_low = int(np.argmin(y_pred_sample))

    return {
        "model": xgb,
        "explainer": explainer,
        "shap_values": shap_values,
        "X_sample": X_sample,
        "feature_names": feature_names,
        "y_pred_sample": y_pred_sample,
        "expected_value": expected_v,
        "idx_high": idx_high,
        "idx_low": idx_low,
    }


def evaluate_model_xai(train_output):
    """
    DSO 5.4 — Generate full XAI dashboard (SHAP plots).

    Parameters
    ----------
    train_output : dict returned by train_model_xai()
    """
    try:
        import shap
    except ImportError:
        import subprocess, sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "shap", "-q"])
        import shap
    import matplotlib.gridspec as gridspec

    shap_values = train_output["shap_values"]
    X_sample = train_output["X_sample"]
    feature_names = train_output["feature_names"]
    expected_value = train_output["expected_value"]
    y_pred_sample = train_output["y_pred_sample"]
    idx_high = train_output["idx_high"]
    idx_low = train_output["idx_low"]
    xgb = train_output["model"]

    # Global summary plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_sample, feature_names=feature_names, plot_type="dot", show=False)
    plt.title("DSO 5.4 — SHAP Summary (Global): Impact on QoS_Probability", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("shap_summary_dot.png", dpi=120, bbox_inches="tight")
    plt.show()

    # Bar plot
    plt.figure(figsize=(9, 5))
    shap.summary_plot(shap_values, X_sample, feature_names=feature_names, plot_type="bar", show=False)
    plt.title("DSO 5.4 — SHAP Global Importance (|mean SHAP|)", fontsize=12, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig("shap_summary_bar.png", dpi=120, bbox_inches="tight")
    plt.show()

    # Waterfall plots for best/worst examples
    for label, idx in [("Best QoS (SLA respected)", idx_high), ("Worst QoS (SLA violated)", idx_low)]:
        exp = shap.Explanation(
            values=shap_values[idx],
            base_values=expected_value,
            data=X_sample.iloc[idx].values,
            feature_names=feature_names,
        )
        plt.figure(figsize=(9, 4))
        shap.plots.waterfall(exp, show=False)
        plt.title(f"SHAP Waterfall — {label} (QoS={y_pred_sample[idx]:.3f})", fontsize=11, fontweight="bold")
        plt.tight_layout()
        fname = f"shap_waterfall_{'high' if idx == idx_high else 'low'}.png"
        plt.savefig(fname, dpi=120, bbox_inches="tight")
        plt.show()
        print(f"📊 Saved → {fname}")

    # Consolidated dashboard
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(
        "🖥️ XAI Dashboard — 6G Network Slicing: QoS_Probability Interpretability",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.45, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])
    mean_abs = np.abs(shap_values).mean(axis=0)
    colors_bar = ["#2196F3" if v == max(mean_abs) else "#90CAF9" for v in mean_abs]
    bars = ax1.barh(feature_names, mean_abs, color=colors_bar)
    ax1.set_xlabel("|mean SHAP|")
    ax1.set_title("① Global Importance", fontweight="bold")
    ax1.invert_yaxis()
    for bar, val in zip(bars, mean_abs):
        ax1.text(bar.get_width() + 0.001, bar.get_y() + bar.get_height() / 2, f"{val:.4f}", va="center", fontsize=9)
    ax1.grid(True, alpha=0.3, axis="x")

    ax2 = fig.add_subplot(gs[0, 1:])
    shap_df = pd.DataFrame(shap_values, columns=feature_names)
    shap_melted = shap_df.melt(var_name="Feature", value_name="SHAP")
    sns.violinplot(data=shap_melted, x="Feature", y="SHAP", palette="Set2", inner="box", ax=ax2)
    ax2.axhline(0, color="black", linewidth=1, linestyle="--")
    ax2.set_title("② SHAP Distribution per Feature", fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="y")

    for ax, idx, label, color in [
        (fig.add_subplot(gs[1, :2]), idx_high, f"③ Best QoS={y_pred_sample[idx_high]:.3f}", "#4CAF50"),
        (fig.add_subplot(gs[1, 2]), idx_low, f"④ Worst QoS={y_pred_sample[idx_low]:.3f}", "#F44336"),
    ]:
        sv = shap_values[idx]
        cum = np.cumsum(np.append(expected_value, sv))
        clrs = ["#4CAF50" if v >= 0 else "#F44336" for v in sv]
        ax.bar(feature_names, sv, bottom=cum[:-1], color=clrs, alpha=0.85, width=0.5)
        ax.axhline(expected_value, color="grey", linestyle=":", linewidth=1.2)
        ax.axhline(cum[-1], color=color, linestyle="--", linewidth=1.5)
        ax.set_title(label, fontweight="bold", fontsize=9)
        ax.set_ylabel("QoS_Probability")
        ax.grid(True, alpha=0.3, axis="y")
        ax.tick_params(axis="x", rotation=30)

    ax5 = fig.add_subplot(gs[2, :])
    shap_hm = pd.DataFrame(shap_values[:30], columns=feature_names)
    sns.heatmap(
        shap_hm.T,
        cmap="RdBu_r",
        center=0,
        xticklabels=[f"ex.{i}" for i in range(30)],
        yticklabels=feature_names,
        linewidths=0.3,
        ax=ax5,
        cbar_kws={"label": "SHAP value"},
    )
    ax5.set_title("⑤ SHAP Matrix — first 30 test examples", fontweight="bold")

    plt.savefig("xai_dashboard_6G.png", dpi=150, bbox_inches="tight")
    plt.show()
    print("✅ Dashboard saved → xai_dashboard_6G.png")


# ─────────────────────────────────────────────
# 6. save_model() / load_model()
# ─────────────────────────────────────────────


def save_model(obj, path):
    """
    Save any Python object (model, scaler, list…) with joblib.

    Parameters
    ----------
    obj  : object to save
    path : file path (e.g. 'models/my_model.joblib')
    """
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    joblib.dump(obj, path)
    size_kb = os.path.getsize(path) / 1024
    print(f"💾 Saved → {path}  ({size_kb:.1f} KB)")


def load_model(path):
    """
    Load a joblib-serialised object.

    Parameters
    ----------
    path : file path

    Returns
    -------
    Loaded object
    """
    obj = joblib.load(path)
    print(f"📂 Loaded ← {path}")
    return obj
