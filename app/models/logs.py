"""
Logging models - operational and ML explainability logs
"""
from datetime import datetime
from app.extensions import db


class IntegrationLog(db.Model):
    """
    IntegrationLog - tracks microservice integration operations
    """
    __tablename__ = 'integration_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False, index=True)
    endpoint = db.Column(db.String(255), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    latency_ms = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f'<IntegrationLog {self.service} {self.status_code}>'


class ShapLog(db.Model):
    """
    ShapLog - SHAP explainability features for ML predictions
    """
    __tablename__ = 'shap_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    slice_id = db.Column(db.String(50), nullable=False, index=True)
    model_version = db.Column(db.String(20), nullable=False)
    features_json = db.Column(db.Text, nullable=False)  # JSON of SHAP values
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<ShapLog {self.slice_id}>'
