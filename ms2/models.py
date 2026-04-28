"""
models.py
=========
SQLAlchemy models for MS-2 Anomaly Detection Service.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Anomaly(db.Model):
    __tablename__ = "anomalies"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id   = db.Column(db.String(50))
    score      = db.Column(db.Float)
    is_anomaly = db.Column(db.Boolean)
    method     = db.Column(db.String(30))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":         self.id,
            "slice_id":   self.slice_id,
            "score":      self.score,
            "is_anomaly": self.is_anomaly,
            "method":     self.method,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
