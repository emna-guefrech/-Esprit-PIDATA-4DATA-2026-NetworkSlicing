"""
models.py
=========
SQLAlchemy models for MS-4 Auth & Admin Service.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(
        db.Enum(
            "network_engineer",
            "data_scientist",
            "noc_operator",
            "system_admin"
        ),
        nullable=False
    )
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.now)
    last_login    = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id":         self.id,
            "username":   self.username,
            "role":       self.role,
            "is_active":  self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S")
                          if self.last_login else None,
        }


class IntegrationLog(db.Model):
    __tablename__ = "integration_logs"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    service     = db.Column(db.String(30))
    endpoint    = db.Column(db.String(100))
    status_code = db.Column(db.Integer)
    latency_ms  = db.Column(db.Integer)
    created_at  = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id":          self.id,
            "service":     self.service,
            "endpoint":    self.endpoint,
            "status_code": self.status_code,
            "latency_ms":  self.latency_ms,
            "created_at":  self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
