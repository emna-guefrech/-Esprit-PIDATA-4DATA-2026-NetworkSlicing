"""
models.py for MS-3 Dashboard
SQLAlchemy models for Alert and Threshold management
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SliceState(db.Model):
    __tablename__ = 'slice_states'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id = db.Column(db.String(50), unique=True, nullable=False)
    pipeline = db.Column(db.String(10), nullable=False)  # 6G, 5G
    qos_score = db.Column(db.Float)
    congestion_level = db.Column(db.String(20))  # Normal, Light, Critical
    is_anomaly = db.Column(db.Boolean, default=False)
    anomaly_score = db.Column(db.Float)
    status = db.Column(db.String(20), default='active')  # active, inactive
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Store original metrics
    latency_budget = db.Column(db.Float)
    slice_latency = db.Column(db.Float)
    packet_loss_budget = db.Column(db.Float)
    slice_packet_loss = db.Column(db.Float)
    jitter_budget = db.Column(db.Float)
    slice_jitter = db.Column(db.Float)
    data_rate_budget = db.Column(db.Float)
    slice_transfer_rate = db.Column(db.Float)
    
    def to_dict(self):
        return {
            'id': self.id,
            'slice_id': self.slice_id,
            'pipeline': self.pipeline,
            'qos_score': self.qos_score,
            'congestion_level': self.congestion_level,
            'is_anomaly': self.is_anomaly,
            'anomaly_score': self.anomaly_score,
            'status': self.status,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'latency_budget': self.latency_budget,
            'slice_latency': self.slice_latency,
            'packet_loss_budget': self.packet_loss_budget,
            'slice_packet_loss': self.slice_packet_loss,
            'jitter_budget': self.jitter_budget,
            'slice_jitter': self.slice_jitter,
            'data_rate_budget': self.data_rate_budget,
            'slice_transfer_rate': self.slice_transfer_rate
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slice_id = db.Column(db.String(50), nullable=True)
    level = db.Column(db.Enum('WARN', 'CRITICAL'), nullable=True)
    message = db.Column(db.Text, nullable=True)
    acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'slice_id': self.slice_id,
            'level': self.level,
            'message': self.message,
            'acknowledged': self.acknowledged,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Threshold(db.Model):
    __tablename__ = 'thresholds'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    metric = db.Column(db.String(50), nullable=True)
    warn_value = db.Column(db.Float, nullable=True)
    critical_value = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric': self.metric,
            'warn_value': self.warn_value,
            'critical_value': self.critical_value
        }
