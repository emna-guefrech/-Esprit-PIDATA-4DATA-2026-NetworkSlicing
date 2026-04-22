"""
main.py
=======
Entry point for the full 5G Network Slice Classification pipeline.

Usage examples
--------------
Run everything:
    python3 main.py --action all

Run a specific step:
    python3 main.py --action prepare
    python3 main.py --action train_rf
    python3 main.py --action evaluate_rf
    python3 main.py --action train_xgb
    python3 main.py --action evaluate_xgb
    python3 main.py --action train_anomaly
    python3 main.py --action evaluate_anomaly
    python3 main.py --action train_online
    python3 main.py --action evaluate_online
    python3 main.py --action save
    python3 main.py --action load
"""

import argparse
from model_pipeline import (
    prepare_data,
    train_model,
    evaluate_model,
    explain_model,
    train_xgboost,
    evaluate_xgboost,
    train_anomaly_models,
    evaluate_anomaly_models,
    train_online_model,
    evaluate_online_model,
    save_model,
    load_model,
)

# ── Global state (shared between steps) ──────────────────────────────────────
data = None  # output of prepare_data()
rf_model = None  # Random Forest
xgb_results = None  # XGBoost results dict
anomaly_results = None  # Anomaly detection results dict
online_results = None  # Online learning results dict


# ── Step runners ─────────────────────────────────────────────────────────────


def run_prepare():
    global data
    print("\n--- STEP 1: Preparing Data ---")
    data = prepare_data(
        train_path="train_dataset.csv",
        test_path="test_dataset.csv",
    )


def run_train_rf():
    global data, rf_model
    if data is None:
        print("[main] Data not ready. Running prepare first...")
        run_prepare()
    print("\n--- STEP 2: Training Random Forest ---")
    rf_model = train_model(
        X_tr=data["X_tr"],
        y_tr=data["y_tr"],
    )


def run_evaluate_rf():
    global data, rf_model
    if rf_model is None:
        print("[main] No RF model found. Training first...")
        run_train_rf()
    print("\n--- STEP 3: Evaluating Random Forest ---")
    evaluate_model(
        model=rf_model,
        X_val=data["X_val"],
        y_val=data["y_val"],
    )

def run_explain():
    global data, rf_model
    if rf_model is None:
        print("[main] No RF model found. Training first...")
        run_train_rf()
    print("\n--- STEP XAI: SHAP + LIME Explainability ---")
    explain_model(
        model         = rf_model,
        X_val         = data["X_val"],
        feature_names = data["feature_names"],
        n_samples     = 200,
        lime_index    = 0,
    )

def run_train_xgb():
    global data, xgb_results
    if data is None:
        print("[main] Data not ready. Running prepare first...")
        run_prepare()
    print("\n--- STEP 4: Training XGBoost (SLA Risk) ---")
    xgb_results = train_xgboost(
        train_raw=data["train_raw"],
        test_raw=data["test_raw"],
    )


def run_evaluate_xgb():
    global xgb_results
    if xgb_results is None:
        print("[main] No XGBoost model found. Training first...")
        run_train_xgb()
    print("\n--- STEP 5: Evaluating XGBoost (SLA Risk) ---")
    evaluate_xgboost(
        model=xgb_results["model"],
        X_val=xgb_results["X_val"],
        y_val=xgb_results["y_val"],
    )


def run_train_anomaly():
    global data, anomaly_results
    if data is None:
        print("[main] Data not ready. Running prepare first...")
        run_prepare()
    print("\n--- STEP 6: Training Anomaly Detection Ensemble ---")
    anomaly_results = train_anomaly_models(
        train_raw=data["train_raw"],
        test_raw=data["test_raw"],
    )


def run_evaluate_anomaly():
    global anomaly_results
    if anomaly_results is None:
        print("[main] No anomaly model found. Training first...")
        run_train_anomaly()
    print("\n--- STEP 7: Evaluating Anomaly Detection Ensemble ---")
    evaluate_anomaly_models(
        ensemble_scores=anomaly_results["ensemble_scores"],
        y_labels=anomaly_results["y_labels"],
        best_threshold=anomaly_results["best_threshold"],
    )


def run_train_online():
    global data, online_results
    if data is None:
        print("[main] Data not ready. Running prepare first...")
        run_prepare()
    print("\n--- STEP 8: Training Online HAT Model ---")
    online_results = train_online_model(
        train_raw=data["train_raw"],
    )


def run_evaluate_online():
    global data, online_results
    if online_results is None:
        print("[main] No online model found. Training first...")
        run_train_online()
    print("\n--- STEP 9: Evaluating Online HAT Model ---")
    evaluate_online_model(
        model=online_results["model"],
        scaler=online_results["scaler"],
        test_raw=data["test_raw"],
    )


def run_save():
    global data, rf_model
    if rf_model is None:
        print("[main] No RF model found. Training first...")
        run_train_rf()
    print("\n--- STEP 10: Saving Random Forest Model ---")
    save_model(
        model=rf_model,
        scaler=data["scaler"],
        model_path="model.pkl",
        scaler_path="scaler.pkl",
    )
    # Save XGBoost if available
    if xgb_results is not None:
        save_model(
            model=xgb_results["model"],
            scaler=data["scaler"],
            model_path="xgb_model.pkl",
            scaler_path="scaler.pkl",
        )


def run_load():
    print("\n--- STEP 11: Loading Saved Model ---")
    loaded_model, loaded_scaler = load_model(
        model_path="model.pkl",
        scaler_path="scaler.pkl",
    )
    print(f"[main] Model type  : {type(loaded_model)}")
    print(f"[main] Scaler type : {type(loaded_scaler)}")


def run_all():
    run_prepare()
    run_train_rf()
    run_evaluate_rf()
    run_explain()
    run_train_xgb()
    run_evaluate_xgb()
    run_train_anomaly()
    run_evaluate_anomaly()
    run_train_online()
    run_evaluate_online()
    run_save()
    run_load()


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="5G Network Slice Classification — Full Pipeline"
    )
    parser.add_argument(
        "--action",
        type=str,
        choices=[
            "prepare",
            "train_rf",
            "evaluate_rf",
            "explain",
            "train_xgb",
            "evaluate_xgb",
            "train_anomaly",
            "evaluate_anomaly",
            "train_online",
            "evaluate_online",
            "save",
            "load",
            "all",
        ],
        default="all",
        help="Which step to run (default: all)",
    )
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"  5G Network Slice Classification — Full Pipeline")
    print(f"  Action : {args.action.upper()}")
    print(f"{'='*55}")

    actions = {
        "prepare": run_prepare,
        "train_rf": run_train_rf,
        "evaluate_rf": run_evaluate_rf,
        "explain": run_explain,  
        "train_xgb": run_train_xgb,
        "evaluate_xgb": run_evaluate_xgb,
        "train_anomaly": run_train_anomaly,
        "evaluate_anomaly": run_evaluate_anomaly,
        "train_online": run_train_online,
        "evaluate_online": run_evaluate_online,
        "save": run_save,
        "load": run_load,
        "all": run_all,
    }

    actions[args.action]()

    print(f"\n{'='*55}")
    print("  Pipeline finished successfully ✅")
    print(f"{'='*55}\n")
