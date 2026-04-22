"""
main.py
=======
CLI entry point for the 6G Network Slicing ML pipeline.

Usage examples:
  python main.py --step prepare
  python main.py --step dso1
  python main.py --step dso52
  python main.py --step dso53
  python main.py --step dso54
  python main.py --step all
"""

import argparse
import os
from model_pipeline import (
    prepare_data,
    train_model_regression,
    evaluate_model_regression,
    train_model_anomaly,
    evaluate_model_anomaly,
    train_model_online,
    evaluate_model_online,
    train_model_xai,
    evaluate_model_xai,
    save_model,
)

# ── File paths (adjust if your CSVs have different names) ─────────────
RAW_CSV = "network_slicing_dataset - v3_6G_OLD.csv"
CONGESTION_CSV = "network_slicing_congestion_final.csv"
FINAL_CSV = "network_slicing_dataset_6G_final.csv"
MODELS_DIR = "models"


def run_prepare():
    print("\n🔷 STEP: Data Preparation")
    df = prepare_data(raw_path=RAW_CSV, output_path="network_slicing_dataset_final.csv")
    print(f"✅ Done. Shape: {df.shape}")


def run_dso1():
    print("\n🔷 STEP: DSO 1 — QoS Probability Regression")
    out = train_model_regression(dataset_path=CONGESTION_CSV)
    evaluate_model_regression(out)
    save_model(out["best_model"], f"{MODELS_DIR}/model_dso1_regression.joblib")
    save_model(out["features"], f"{MODELS_DIR}/features_dso1.joblib")


def run_dso52():
    print("\n🔷 STEP: DSO 5.2 — Anomaly Detection")
    out = train_model_anomaly(dataset_path=CONGESTION_CSV)
    evaluate_model_anomaly(out)
    save_model(out["model"], f"{MODELS_DIR}/model_dso52_isoforest.joblib")
    save_model(out["scaler"], f"{MODELS_DIR}/scaler_dso52.joblib")
    save_model(out["features"], f"{MODELS_DIR}/features_dso52.joblib")


def run_dso53():
    print("\n🔷 STEP: DSO 5.3 — Online Learning")
    out = train_model_online(dataset_path=CONGESTION_CSV, n_batches=10)
    evaluate_model_online(out)
    save_model(out["model"], f"{MODELS_DIR}/model_dso53_sgd.joblib")
    save_model(out["scaler"], f"{MODELS_DIR}/scaler_dso53.joblib")
    save_model(out["encoder"], f"{MODELS_DIR}/encoder_dso53.joblib")
    save_model(out["features"], f"{MODELS_DIR}/features_dso53.joblib")


def run_dso54():
    print("\n🔷 STEP: DSO 5.4 — XAI Dashboard")
    out = train_model_xai(dataset_path=CONGESTION_CSV)
    evaluate_model_xai(out)
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs("xai_artifacts", exist_ok=True)
    save_model(out["model"], f"{MODELS_DIR}/model_dso54_xgboost_xai.joblib")
    save_model(out["explainer"], "xai_artifacts/shap_explainer_dso54.joblib")
    save_model(out["feature_names"], "xai_artifacts/features_dso54.joblib")
    import numpy as np

    np.save("xai_artifacts/shap_values_test.npy", out["shap_values"])
    out["X_sample"].to_csv("xai_artifacts/X_shap_sample.csv", index=False)
    print("✅ All XAI artifacts saved.")


def run_all():
    run_prepare()
    run_dso1()
    run_dso52()
    run_dso53()
    run_dso54()
    print("\n🎉 Full pipeline complete!")


# ── CLI ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="6G Network Slicing ML Pipeline")
    parser.add_argument(
        "--step", choices=["prepare", "dso1", "dso52", "dso53", "dso54", "all"], required=True, help="Which step to run"
    )
    args = parser.parse_args()

    os.makedirs(MODELS_DIR, exist_ok=True)

    steps = {
        "prepare": run_prepare,
        "dso1": run_dso1,
        "dso52": run_dso52,
        "dso53": run_dso53,
        "dso54": run_dso54,
        "all": run_all,
    }
    steps[args.step]()
