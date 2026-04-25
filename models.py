"""
models.py
=========
SQLAlchemy models for MS-1 Prediction Service.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Prediction(db.Model):
    __tablename__ = "predictions"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id         = db.Column(db.String(50))
    congestion_level = db.Column(db.Enum("Normal", "Light", "Critical"))
    qos_score        = db.Column(db.Float)
    features_json    = db.Column(db.Text)
    created_at       = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":               self.id,
            "slice_id":         self.slice_id,
            "congestion_level": self.congestion_level,
            "qos_score":        self.qos_score,
            "features_json":    self.features_json,
            "created_at":       self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Anomaly(db.Model):
    __tablename__ = "anomalies"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id   = db.Column(db.String(50))
    score      = db.Column(db.Float)
    is_anomaly = db.Column(db.Boolean)
    method     = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.now)


class Alert(db.Model):
    __tablename__ = "alerts"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id     = db.Column(db.String(50))
    level        = db.Column(db.Enum("WARN", "CRITICAL"))
    message      = db.Column(db.Text)
    acknowledged = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.now)


class ModelVersion(db.Model):
    __tablename__ = "model_versions"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name = db.Column(db.String(50))
    version    = db.Column(db.String(20))
    r2_score   = db.Column(db.Float)
    rmse       = db.Column(db.Float)
    accuracy   = db.Column(db.Float)
    trained_at = db.Column(db.DateTime, default=datetime.now)
