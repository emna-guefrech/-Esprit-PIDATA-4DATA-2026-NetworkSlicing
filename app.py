from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import json
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/network_slicing'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
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

# API Routes
@app.route('/dashboard/slices', methods=['GET'])
def get_dashboard_slices():
    """Get status of all active slices (aggregated from MS-1)"""
    try:
        # Mock data for MS-1 slices service
        # In real implementation, this would call MS-1 API
        slices_data = [
            {
                'slice_id': 'slice_001',
                'status': 'ACTIVE',
                'qos_metrics': {
                    'bandwidth': 85.5,
                    'latency': 12.3,
                    'jitter': 2.1,
                    'packet_loss': 0.01
                },
                'ue_count': 45,
                'created_at': '2026-04-23T10:30:00Z'
            },
            {
                'slice_id': 'slice_002',
                'status': 'ACTIVE',
                'qos_metrics': {
                    'bandwidth': 92.1,
                    'latency': 8.7,
                    'jitter': 1.5,
                    'packet_loss': 0.005
                },
                'ue_count': 32,
                'created_at': '2026-04-23T11:15:00Z'
            },
            {
                'slice_id': 'slice_003',
                'status': 'DEGRADED',
                'qos_metrics': {
                    'bandwidth': 65.2,
                    'latency': 25.8,
                    'jitter': 4.3,
                    'packet_loss': 0.025
                },
                'ue_count': 18,
                'created_at': '2026-04-23T09:45:00Z'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'data': slices_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alerts', methods=['GET'])
def get_dashboard_alerts():
    """Get active alerts (WARN/CRITICAL)"""
    try:
        alerts = Alert.query.filter_by(acknowledged=False).order_by(Alert.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'data': [alert.to_dict() for alert in alerts],
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/threshold', methods=['POST'])
def configure_threshold():
    """Configure monitoring thresholds"""
    try:
        data = request.get_json()
        
        if not data or 'metric' not in data:
            return jsonify({'status': 'error', 'message': 'Missing metric field'}), 400
        
        # Check if threshold already exists
        existing = Threshold.query.filter_by(metric=data['metric']).first()
        if existing:
            existing.warn_value = data.get('warn_value')
            existing.critical_value = data.get('critical_value')
        else:
            new_threshold = Threshold(
                metric=data['metric'],
                warn_value=data.get('warn_value'),
                critical_value=data.get('critical_value')
            )
            db.session.add(new_threshold)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Threshold configured successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/ack', methods=['POST'])
def acknowledge_alert():
    """Acknowledge an alert"""
    try:
        data = request.get_json()
        
        if not data or 'alert_id' not in data:
            return jsonify({'status': 'error', 'message': 'Missing alert_id field'}), 400
        
        alert = Alert.query.get(data['alert_id'])
        if not alert:
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
        
        alert.acknowledged = True
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert acknowledged successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/thresholds', methods=['GET'])
def get_thresholds():
    """Get all configured thresholds"""
    try:
        thresholds = Threshold.query.all()
        return jsonify({
            'status': 'success',
            'data': [threshold.to_dict() for threshold in thresholds]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Dashboard UI Routes
@app.route('/')
def dashboard():
    """Main NOC Operator Dashboard"""
    return render_template('dashboard.html')

@app.route('/api/qos-history')
def get_qos_history():
    """Get historical QoS data for charts"""
    try:
        # Mock historical data
        # In real implementation, this would aggregate data from MS-2
        history_data = {
            'timestamps': [],
            'bandwidth': [],
            'latency': [],
            'packet_loss': []
        }
        
        # Generate 24 hours of mock data (hourly points)
        base_time = datetime.utcnow() - timedelta(hours=24)
        for i in range(25):
            timestamp = base_time + timedelta(hours=i)
            history_data['timestamps'].append(timestamp.isoformat())
            history_data['bandwidth'].append(75 + (i % 10) * 2)
            history_data['latency'].append(10 + (i % 5) * 2)
            history_data['packet_loss'].append(0.01 + (i % 3) * 0.005)
        
        return jsonify({
            'status': 'success',
            'data': history_data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()
    
    # Initialize default thresholds if none exist
    if Threshold.query.count() == 0:
        default_thresholds = [
            Threshold(metric='bandwidth', warn_value=70.0, critical_value=50.0),
            Threshold(metric='latency', warn_value=20.0, critical_value=50.0),
            Threshold(metric='packet_loss', warn_value=0.02, critical_value=0.05),
            Threshold(metric='jitter', warn_value=3.0, critical_value=5.0)
        ]
        for threshold in default_thresholds:
            db.session.add(threshold)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)
