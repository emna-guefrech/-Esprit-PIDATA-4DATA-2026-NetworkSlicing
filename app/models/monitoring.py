"""
Monitoring models - minimal mapping for dashboard display
Tables: alerts, thresholds, predictions, anomalies, model_versions
These are read-only from the dashboard perspective
"""
from datetime import datetime
from app.extensions import db


class Alert(db.Model):
    """
    Alert model - represents system alerts
    Minimal schema for dashboard display
    """
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    slice_id = db.Column(db.String(50), nullable=False, index=True)
    level = db.Column(db.String(20), nullable=False)  # WARN, CRITICAL
    message = db.Column(db.Text, nullable=False)
    acknowledged = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Alert {self.slice_id} {self.level}>'


class Threshold(db.Model):
    """
    Threshold model - configuration for metric thresholds
    Used for alert triggering and monitoring
    """
    __tablename__ = 'thresholds'
    
    id = db.Column(db.Integer, primary_key=True)
    metric = db.Column(db.String(100), nullable=False, unique=True, index=True)
    warn_value = db.Column(db.Float, nullable=False)
    critical_value = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Threshold {self.metric}>'


class Prediction(db.Model):
    """
    Prediction model - ML model predictions for network slices
    Read-only, used for display and analysis
    """
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    slice_id = db.Column(db.String(50), nullable=False, index=True)
    congestion_level = db.Column(db.String(50), nullable=False)  # Normal, Light, Critical
    qos_score = db.Column(db.Float, nullable=False)
    features_json = db.Column(db.Text)  # JSON features used in prediction
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Prediction {self.slice_id} {self.congestion_level}>'


class Anomaly(db.Model):
    """
    Anomaly model - anomaly detection results
    """
    __tablename__ = 'anomalies'
    
    id = db.Column(db.Integer, primary_key=True)
    slice_id = db.Column(db.String(50), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    is_anomaly = db.Column(db.Boolean, default=False)
    method = db.Column(db.String(50))  # Detection method used
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Anomaly {self.slice_id} score={self.score}>'


class ModelVersion(db.Model):
    """
    ModelVersion model - tracks ML model performance and versions
    """
    __tablename__ = 'model_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    r2_score = db.Column(db.Float)
    rmse = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    trained_at = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<ModelVersion {self.model_name} v{self.version}>'
