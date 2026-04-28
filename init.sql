-- ══════════════════════════════════════════════════════════════════
-- init.sql — Shared database schema for all microservices
-- ══════════════════════════════════════════════════════════════════

USE network_slicing;

CREATE TABLE IF NOT EXISTS predictions (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    slice_id         VARCHAR(50),
    congestion_level ENUM('Normal','Light','Critical'),
    qos_score        FLOAT,
    features_json    TEXT,
    created_at       DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS anomalies (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    slice_id   VARCHAR(50),
    score      FLOAT,
    is_anomaly BOOLEAN,
    method     VARCHAR(30),
    created_at DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    slice_id     VARCHAR(50),
    level        ENUM('WARN','CRITICAL'),
    message      TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at   DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS thresholds (
    id             INT AUTO_INCREMENT PRIMARY KEY,
    metric         VARCHAR(50) UNIQUE,
    warn_value     FLOAT,
    critical_value FLOAT
);

CREATE TABLE IF NOT EXISTS users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) UNIQUE,
    password_hash VARCHAR(255),
    role          ENUM('network_engineer','data_scientist',
                       'noc_operator','system_admin'),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    DATETIME DEFAULT NOW(),
    last_login    DATETIME
);

CREATE TABLE IF NOT EXISTS integration_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    service     VARCHAR(30),
    endpoint    VARCHAR(100),
    status_code INT,
    latency_ms  INT,
    created_at  DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS model_versions (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(50),
    version    VARCHAR(20),
    r2_score   FLOAT,
    rmse       FLOAT,
    accuracy   FLOAT,
    trained_at DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shap_logs (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    slice_id      VARCHAR(50),
    model_version VARCHAR(20),
    features_json TEXT,
    created_at    DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS slice_states (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    slice_id         VARCHAR(50) UNIQUE,
    pipeline         VARCHAR(10),
    qos_score        FLOAT,
    congestion_level VARCHAR(20),
    is_anomaly       BOOLEAN DEFAULT FALSE,
    anomaly_score    FLOAT,
    status           VARCHAR(20) DEFAULT 'active',
    last_updated     DATETIME DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drift_logs (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    model_name   VARCHAR(50),
    drift_score  FLOAT,
    drift_status VARCHAR(20),
    details_json TEXT,
    checked_at   DATETIME DEFAULT NOW()
);

-- Default thresholds
INSERT IGNORE INTO thresholds (metric, warn_value, critical_value) VALUES
    ('qos_score',      0.5, 0.3),
    ('anomaly_score',  0.4, 0.65),
    ('congestion_level', 1.0, 2.0);
