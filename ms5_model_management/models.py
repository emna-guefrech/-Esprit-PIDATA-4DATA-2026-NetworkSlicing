"""
models.py
=========
SQLAlchemy models for MS-5 Model Management Service.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class ModelVersion(db.Model):
    __tablename__ = "model_versions"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name = db.Column(db.String(50))
    version    = db.Column(db.String(20))
    r2_score   = db.Column(db.Float)
    rmse       = db.Column(db.Float)
    accuracy   = db.Column(db.Float)
    trained_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":         self.id,
            "model_name": self.model_name,
            "version":    self.version,
            "r2_score":   self.r2_score,
            "rmse":       self.rmse,
            "accuracy":   self.accuracy,
            "trained_at": self.trained_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class ShapLog(db.Model):
    __tablename__ = "shap_logs"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id      = db.Column(db.String(50))
    model_version = db.Column(db.String(20))
    features_json = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":            self.id,
            "slice_id":      self.slice_id,
            "model_version": self.model_version,
            "features_json": self.features_json,
            "created_at":    self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }


class DriftLog(db.Model):
    __tablename__ = "drift_logs"

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_name   = db.Column(db.String(50))
    drift_score  = db.Column(db.Float)
    drift_status = db.Column(db.String(20))
    details_json = db.Column(db.Text)
    checked_at   = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":           self.id,
            "model_name":   self.model_name,
            "drift_score":  self.drift_score,
            "drift_status": self.drift_status,
            "details_json": self.details_json,
            "checked_at":   self.checked_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
