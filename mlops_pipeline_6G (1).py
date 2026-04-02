"""
================================================================================
  MLOps Pipeline — Network Slicing 6G
  Projet  : PI 4DATA — Phase 2
  Auteur  : Groupe [votre nom]
================================================================================

Description
-----------
Pipeline MLOps complet pour la prédiction de la QoS dans les réseaux 6G.
Deux tâches sont automatisées :
  • SLA_Respected  : classification binaire  (0/1)
  • Slice Type     : classification multiclasse (5 classes)

Étapes automatisées :
  1. Chargement & validation des données
  2. Prétraitement & normalisation
  3. Entraînement de 3 modèles (Logistic Regression, Random Forest, Gradient Boosting)
  4. Évaluation (Accuracy, F1, Cross-Validation)
  5. Sélection automatique du meilleur modèle
  6. Sauvegarde + versioning (model registry JSON)
  7. Génération de rapports visuels
  8. Interface d'inférence sur nouvelles données

Utilisation
-----------
  # Exécuter le pipeline complet :
  python mlops_pipeline_6G.py

  # Importer uniquement l'inférence :
  from mlops_pipeline_6G import predict
  predictions = predict(new_data, task='sla')
"""

# ==============================================================================
# 0. IMPORTS
# ==============================================================================
import os, json, time, logging, warnings, hashlib, datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, f1_score,
)

warnings.filterwarnings("ignore")

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# ==============================================================================
# 1. CONFIGURATION GLOBALE
# ==============================================================================

CONFIG = {
    "data_path":     "mon_nouveau_dataset_6G.csv",
    "models_dir":    "models/",
    "logs_dir":      "logs/",
    "reports_dir":   "reports/",
    "registry_path": "models/model_registry.json",

    "sla_features": [
        "Latency_Gap", "Packet_Loss_Gap", "Jitter_Gap", "Rate_Gap",
    ],
    "sla_target": "SLA_Respected",

    "slice_features": [
        "Packet Loss Budget", "Latency Budget (\u03bcs)", "Jitter Budget (\u03bcs)",
        "Data Rate Budget (Gbps)", "Required Mobility",
        "Required Connectivity", "Slice Available Transfer Rate (Gbps)",
    ],
    "slice_target": "Slice Type",

    "test_size":    0.2,
    "random_state": 42,
    "cv_folds":     5,
}

# ==============================================================================
# 2. LOGGING
# ==============================================================================

def setup_logger(name: str) -> logging.Logger:
    os.makedirs(CONFIG["logs_dir"], exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file  = os.path.join(CONFIG["logs_dir"], f"{name}_{timestamp}.log")
    logger    = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fmt = logging.Formatter("[%(asctime)s] %(levelname)-8s %(message)s", datefmt="%H:%M:%S")
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        sh.stream = open(sh.stream.fileno(), mode='w', encoding='utf-8', buffering=1, closefd=False) if hasattr(sh.stream, 'fileno') else sh.stream
        logger.addHandler(sh)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

logger = setup_logger("mlops_6G")

# ==============================================================================
# 3. ETAPE 1 — CHARGEMENT & VALIDATION
# ==============================================================================

def load_and_validate(data_path: str) -> pd.DataFrame:
    """
    Charge le CSV, valide les colonnes requises, detecte les
    valeurs manquantes et les doublons.
    """
    logger.info("=" * 65)
    logger.info("  ETAPE 1 — Chargement & Validation des donnees")
    logger.info("=" * 65)

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Fichier introuvable : {data_path}")

    df = pd.read_csv(data_path)
    logger.info(f"  OK Dataset charge : {df.shape[0]:,} lignes x {df.shape[1]} colonnes")

    with open(data_path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()
    logger.info(f"  MD5 : {md5}")

    required = (
        CONFIG["sla_features"] + [CONFIG["sla_target"]] +
        CONFIG["slice_features"] + [CONFIG["slice_target"]]
    )
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes absentes : {missing_cols}")
    logger.info("  OK Toutes les colonnes requises sont presentes")

    null_total = df.isnull().sum().sum()
    if null_total:
        logger.warning(f"  WARN {null_total} valeurs manquantes detectees")
    else:
        logger.info("  OK Aucune valeur manquante")

    n_dup = df.duplicated().sum()
    if n_dup:
        df = df.drop_duplicates()
        logger.warning(f"  WARN {n_dup} doublons supprimes")
    else:
        logger.info("  OK Aucun doublon")

    sla_dist   = df[CONFIG["sla_target"]].value_counts(normalize=True).round(3).to_dict()
    slice_dist = df[CONFIG["slice_target"]].value_counts().to_dict()
    logger.info(f"  SLA_Respected : {sla_dist}")
    logger.info(f"  Slice Type    : {slice_dist}")

    return df

# ==============================================================================
# 4. ETAPE 2 — PRETRAITEMENT
# ==============================================================================

def preprocess(df: pd.DataFrame, task: str = "sla"):
    """
    Selectionne les features, impute par mediane, normalise
    (StandardScaler) et divise en train/test stratifie.

    task : 'sla' ou 'slice'
    Retourne : X_train, X_test, y_train, y_test, scaler, feature_names
    """
    logger.info("-" * 50)
    logger.info(f"  ETAPE 2 — Pretraitement  [tache : {task.upper()}]")
    logger.info("-" * 50)

    features = CONFIG["sla_features"]   if task == "sla" else CONFIG["slice_features"]
    target   = CONFIG["sla_target"]     if task == "sla" else CONFIG["slice_target"]

    X = df[features].copy()
    y = df[target].copy()

    for col in X.columns:
        n_null = X[col].isnull().sum()
        if n_null:
            X[col].fillna(X[col].median(), inplace=True)
            logger.info(f"  Imputation mediane : '{col}' ({n_null} valeurs)")

    scaler  = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=features)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y,
        test_size=CONFIG["test_size"],
        random_state=CONFIG["random_state"],
        stratify=y,
    )

    logger.info(f"  OK Train : {len(X_train):,}  /  Test : {len(X_test):,}")
    logger.info(f"  OK Features : {features}")
    return X_train, X_test, y_train, y_test, scaler, features

# ==============================================================================
# 5. ETAPE 3 — DEFINITION DES MODELES
# ==============================================================================

def get_models(task: str = "sla") -> dict:
    """
    Retourne 3 modeles configures.
    class_weight='balanced' pour gerer le desequilibre des classes.
    XGBoost si disponible, sinon Gradient Boosting (sklearn).
    """
    if XGBOOST_AVAILABLE:
        boost = XGBClassifier(
            use_label_encoder=False,
            eval_metric="logloss" if task == "sla" else "mlogloss",
            random_state=CONFIG["random_state"],
            n_estimators=100, learning_rate=0.1, verbosity=0,
        )
        boost_name = "XGBoost"
    else:
        boost = GradientBoostingClassifier(
            n_estimators=100, learning_rate=0.1,
            random_state=CONFIG["random_state"],
        )
        boost_name = "Gradient Boosting"

    return {
        "Logistic Regression": LogisticRegression(
            max_iter=2000, random_state=CONFIG["random_state"],
            class_weight="balanced", solver="lbfgs",
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=15,
            random_state=CONFIG["random_state"],
            class_weight="balanced", n_jobs=-1,
        ),
        boost_name: boost,
    }

# ==============================================================================
# 6. ETAPE 4 — ENTRAINEMENT & EVALUATION
# ==============================================================================

def train_and_evaluate(X_train, X_test, y_train, y_test, task: str = "sla") -> dict:
    """
    Entraine chaque modele, calcule Accuracy / F1 / Cross-Validation.
    Retourne un dict ordonne par F1-score decroissant.
    """
    logger.info("-" * 50)
    logger.info(f"  ETAPE 3 — Entrainement & Evaluation  [tache : {task.upper()}]")
    logger.info("-" * 50)

    is_binary  = (task == "sla")
    average    = "binary" if is_binary else "macro"
    cv_scoring = "f1"     if is_binary else "f1_macro"

    models  = get_models(task)
    results = {}

    for name, model in models.items():
        logger.info(f"  >> {name} ...")
        t0 = time.time()

        model.fit(X_train, y_train)
        elapsed = round(time.time() - t0, 3)

        y_pred = model.predict(X_test)
        acc    = accuracy_score(y_test, y_pred)
        f1     = f1_score(y_test, y_pred, average=average, zero_division=0)

        cv = StratifiedKFold(n_splits=CONFIG["cv_folds"], shuffle=True,
                             random_state=CONFIG["random_state"])
        cv_scores = cross_val_score(model, X_train, y_train,
                                    cv=cv, scoring=cv_scoring, n_jobs=-1)

        results[name] = {
            "model":      model,
            "train_time": elapsed,
            "accuracy":   round(acc, 4),
            "f1_score":   round(f1,  4),
            "cv_mean":    round(cv_scores.mean(), 4),
            "cv_std":     round(cv_scores.std(),  4),
            "y_pred":     y_pred,
            "report":     classification_report(y_test, y_pred, zero_division=0),
        }

        logger.info(
            f"     Acc={acc:.4f}  F1={f1:.4f}  "
            f"CV={cv_scores.mean():.4f}+/-{cv_scores.std():.4f}  "
            f"({elapsed}s)"
        )

    return dict(sorted(results.items(), key=lambda x: x[1]["f1_score"], reverse=True))

# ==============================================================================
# 7. ETAPE 5 — SELECTION DU MEILLEUR MODELE
# ==============================================================================

def select_best_model(results: dict) -> tuple:
    """
    Selectionne le modele avec le meilleur F1-score.
    Retourne (nom, modele, metriques).
    """
    logger.info("-" * 50)
    logger.info("  ETAPE 4 — Selection du meilleur modele")
    logger.info("-" * 50)

    best_name = list(results.keys())[0]
    info      = results[best_name]

    logger.info(f"  BEST : {best_name}")
    logger.info(f"     F1-Score : {info['f1_score']}")
    logger.info(f"     Accuracy : {info['accuracy']}")
    logger.info(f"     CV       : {info['cv_mean']} +/- {info['cv_std']}")
    logger.info(f"\n  Rapport complet :\n{info['report']}")

    return best_name, info["model"], {
        "accuracy": info["accuracy"],
        "f1_score": info["f1_score"],
        "cv_mean":  info["cv_mean"],
        "cv_std":   info["cv_std"],
    }

# ==============================================================================
# 8. ETAPE 6 — SAUVEGARDE & VERSIONING
# ==============================================================================

def save_model(model, scaler, features, task, model_name, metrics) -> str:
    """
    Sauvegarde modele + scaler avec versioning incremental.
    Met a jour le registre JSON (model_registry.json).
    Retourne le chemin du fichier modele.
    """
    logger.info("-" * 50)
    logger.info("  ETAPE 5 — Sauvegarde & Versioning")
    logger.info("-" * 50)

    os.makedirs(CONFIG["models_dir"], exist_ok=True)
    version    = _next_version(task)
    timestamp  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name  = model_name.lower().replace(" ", "_")

    model_path  = os.path.join(CONFIG["models_dir"], f"{task}_{safe_name}_v{version}.pkl")
    scaler_path = os.path.join(CONFIG["models_dir"], f"{task}_scaler_v{version}.pkl")

    joblib.dump(model,  model_path)
    joblib.dump(scaler, scaler_path)

    logger.info(f"  Modele  -> {model_path}")
    logger.info(f"  Scaler  -> {scaler_path}")

    entry = {
        "version": version, "task": task, "model_name": model_name,
        "timestamp": timestamp, "model_path": model_path,
        "scaler_path": scaler_path, "features": features,
        "metrics": metrics, "status": "production",
    }
    _update_registry(entry, task)
    logger.info(f"  Registre mis a jour — v{version} en production")
    return model_path

def _next_version(task: str) -> int:
    rp = CONFIG["registry_path"]
    if not os.path.exists(rp):
        return 1
    with open(rp) as f:
        reg = json.load(f)
    return max((e["version"] for e in reg.get(task, [])), default=0) + 1

def _update_registry(entry: dict, task: str):
    rp = CONFIG["registry_path"]
    os.makedirs(os.path.dirname(rp), exist_ok=True)
    reg = {}
    if os.path.exists(rp):
        with open(rp, encoding="utf-8") as f:
            reg = json.load(f)
    reg.setdefault(task, [])
    for old in reg[task]:
        if old.get("status") == "production":
            old["status"] = "archived"
    reg[task].append(entry)
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)

# ==============================================================================
# 9. ETAPE 7 — RAPPORTS VISUELS
# ==============================================================================

def generate_report(results: dict, y_test, task: str):
    """
    Genere et sauvegarde :
      - CSV de comparaison des metriques
      - Matrices de confusion (PNG)
      - Graphique en barres des F1-scores (PNG)
    """
    logger.info("-" * 50)
    logger.info("  ETAPE 6 — Generation des rapports")
    logger.info("-" * 50)

    os.makedirs(CONFIG["reports_dir"], exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Tableau CSV
    rows = [{
        "Modele": n, "Accuracy": i["accuracy"], "F1-Score": i["f1_score"],
        "CV Mean": i["cv_mean"], "CV Std": i["cv_std"],
        "Temps_train_s": i["train_time"],
    } for n, i in results.items()]
    summary_df = pd.DataFrame(rows)
    csv_out = os.path.join(CONFIG["reports_dir"], f"{task}_comparison_{ts}.csv")
    summary_df.to_csv(csv_out, index=False)
    logger.info(f"  CSV -> {csv_out}")
    print("\n" + summary_df.to_string(index=False) + "\n")

    # Matrices de confusion
    n_models = len(results)
    fig, axes = plt.subplots(1, n_models, figsize=(6 * n_models, 5))
    axes = axes if n_models > 1 else [axes]
    for ax, (name, info) in zip(axes, results.items()):
        cm = confusion_matrix(y_test, info["y_pred"])
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, linewidths=0.5)
        ax.set_title(f"{name}\nAcc={info['accuracy']}  F1={info['f1_score']}", fontsize=10)
        ax.set_xlabel("Predit"); ax.set_ylabel("Reel")
    plt.suptitle(f"Matrices de Confusion — {task.upper()}", fontsize=13, fontweight="bold")
    plt.tight_layout()
    cm_out = os.path.join(CONFIG["reports_dir"], f"{task}_confusion_{ts}.png")
    plt.savefig(cm_out, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"  Matrices de confusion -> {cm_out}")

    # Barplot F1
    names  = list(results.keys())
    f1s    = [results[n]["f1_score"] for n in names]
    cvs    = [results[n]["cv_mean"]  for n in names]
    colors = ["#1565C0" if i == 0 else "#90CAF9" for i in range(len(names))]
    fig, ax = plt.subplots(figsize=(8, 4))
    y_pos   = np.arange(len(names))
    bars    = ax.barh(y_pos, f1s, color=colors, height=0.4, label="F1 Test")
    ax.barh(y_pos - 0.25, cvs, height=0.2, color="#B0BEC5", label="F1 CV (mean)")
    ax.set_yticks(y_pos); ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("F1-Score", fontsize=11)
    ax.set_title(f"Comparaison des modeles — {task.upper()}", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9); ax.grid(axis="x", alpha=0.3); ax.set_xlim(0, 1.1)
    for bar, v in zip(bars, f1s):
        ax.text(v + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{v:.4f}", va="center", fontsize=9)
    plt.tight_layout()
    bar_out = os.path.join(CONFIG["reports_dir"], f"{task}_f1_barplot_{ts}.png")
    plt.savefig(bar_out, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"  Barplot F1 -> {bar_out}")

# ==============================================================================
# 10. ETAPE 8 — INFERENCE SUR NOUVELLES DONNEES
# ==============================================================================

def predict(data: pd.DataFrame, task: str) -> np.ndarray:
    """
    Charge le modele en production depuis le registre et predit
    sur de nouvelles donnees.

    Parametres
    ----------
    data : pd.DataFrame contenant les features requises
    task : 'sla' ou 'slice'

    Exemple
    -------
    >>> preds = predict(new_data, task='sla')
    """
    rp = CONFIG["registry_path"]
    if not os.path.exists(rp):
        raise FileNotFoundError("Registre introuvable. Lancez d'abord run_pipeline().")

    with open(rp, encoding="utf-8") as f:
        registry = json.load(f)

    prod = [e for e in registry.get(task, []) if e["status"] == "production"]
    if not prod:
        raise RuntimeError(f"Aucun modele en production pour la tache '{task}'.")

    entry  = prod[-1]
    model  = joblib.load(entry["model_path"])
    scaler = joblib.load(entry["scaler_path"])

    logger.info(f"  Inference [{task.upper()}] — {entry['model_name']} v{entry['version']}")

    X_scaled = scaler.transform(data[entry["features"]].copy())
    return model.predict(X_scaled)

# ==============================================================================
# 11. PIPELINE PRINCIPAL
# ==============================================================================

def run_pipeline(task: str = "sla") -> tuple:
    """
    Execute le pipeline MLOps complet de bout en bout.

    Parametres
    ----------
    task : 'sla' (binaire) ou 'slice' (multiclasse)

    Retourne
    --------
    (results_dict, best_model_name)
    """
    logger.info("\n" + "=" * 65)
    logger.info(f"  PIPELINE MLOps 6G — Tache : {task.upper()}")
    logger.info(f"  Demarre le : {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    logger.info("=" * 65)

    df                                              = load_and_validate(CONFIG["data_path"])
    X_train, X_test, y_train, y_test, scaler, feats = preprocess(df, task)
    results                                         = train_and_evaluate(X_train, X_test, y_train, y_test, task)
    best_name, best_model, metrics                  = select_best_model(results)

    save_model(
        model=best_model, scaler=scaler, features=feats,
        task=task, model_name=best_name, metrics=metrics,
    )
    generate_report(results, y_test, task)

    logger.info("=" * 65)
    logger.info(f"  Pipeline '{task.upper()}' termine avec succes")
    logger.info("=" * 65)
    return results, best_name

# ==============================================================================
# 12. POINT D'ENTREE
# ==============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  MLOps Pipeline — Network Slicing 6G")
    print("=" * 65)
    print(f"  XGBoost : {'disponible' if XGBOOST_AVAILABLE else 'absent -> Gradient Boosting utilise'}")

    results_sla,   best_sla   = run_pipeline(task="sla")
    results_slice, best_slice = run_pipeline(task="slice")

    print("\n" + "=" * 65)
    print("  RESUME FINAL")
    print("=" * 65)
    print(f"  Tache SLA    : {best_sla}  |  F1 = {results_sla[best_sla]['f1_score']}")
    print(f"  Tache Slice  : {best_slice}  |  F1 = {results_slice[best_slice]['f1_score']}")
    print("\n  Fichiers generes :")
    print("    models/                    -> .pkl (modeles + scalers)")
    print("    models/model_registry.json -> registre des versions")
    print("    reports/                   -> CSV + graphiques PNG")
    print("    logs/                      -> journal d'execution .log")
    print("=" * 65)
