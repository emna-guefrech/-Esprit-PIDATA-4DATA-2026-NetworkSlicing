"""
models.py
=========
SQLAlchemy models for MS-3 Dashboard & Alerts Service.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Alert(db.Model):
    __tablename__ = "alerts"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id     = db.Column(db.String(50))
    level        = db.Column(db.Enum("WARN", "CRITICAL"))
    message      = db.Column(db.Text)
    acknowledged = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":           self.id,
            "slice_id":     self.slice_id,
            "level":        self.level,
            "message":      self.message,
            "acknowledged": self.acknowledged,
            "created_at":   self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class Threshold(db.Model):
    __tablename__ = "thresholds"

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    metric         = db.Column(db.String(50), unique=True)
    warn_value     = db.Column(db.Float)
    critical_value = db.Column(db.Float)

    def to_dict(self):
        return {
            "id":             self.id,
            "metric":         self.metric,
            "warn_value":     self.warn_value,
            "critical_value": self.critical_value,
        }


class SliceState(db.Model):
    __tablename__ = "slice_states"

    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id         = db.Column(db.String(50), unique=True)
    pipeline         = db.Column(db.String(10))
    qos_score        = db.Column(db.Float)
    congestion_level = db.Column(db.String(20))
    is_anomaly       = db.Column(db.Boolean, default=False)
    anomaly_score    = db.Column(db.Float)
    status           = db.Column(db.String(20), default="active")
    last_updated     = db.Column(db.DateTime, default=datetime.now,
                                  onupdate=datetime.now)

    def to_dict(self):
        return {
            "slice_id":         self.slice_id,
            "pipeline":         self.pipeline,
            "qos_score":        self.qos_score,
            "congestion_level": self.congestion_level,
            "is_anomaly":       self.is_anomaly,
            "anomaly_score":    self.anomaly_score,
            "status":           self.status,
            "last_updated":     self.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }
