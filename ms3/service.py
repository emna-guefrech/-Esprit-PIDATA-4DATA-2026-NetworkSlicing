"""
MS-3: Dashboard & Alerts Service
Network Slicing Microservice - Real-time Dashboard and Alert Management
Author: Network Slicing Team
Service: Dashboard & Alerts (MS-3)
Port: 5003
"""

from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask App for MS-3
app = Flask('MS3-Dashboard-Service')

# Service Configuration
SERVICE_NAME = "MS-3 Dashboard & Alerts Service"
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = 5003

# Database configuration
# Use MySQL with existing database
import os
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/network_slicing_'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info("MS-3: Using existing MySQL database: network_slicing_")

db = SQLAlchemy(app)

# Alert Generation Function
def check_and_generate_alerts(slices_data):
    """
    Check slice metrics against thresholds and generate alerts automatically
    """
    try:
        # Get all configured thresholds
        thresholds = Threshold.query.all()
        threshold_dict = {t.metric: {'warn': t.warn_value, 'critical': t.critical_value} for t in thresholds}
        
        for slice_data in slices_data:
            slice_id = slice_data['slice_id']
            qos_metrics = slice_data['qos_metrics']
            
            # Check each metric against thresholds
            for metric, value in qos_metrics.items():
                if metric in threshold_dict:
                    threshold = threshold_dict[metric]
                    
                    # Check for critical alert
                    if is_critical_alert(metric, value, threshold['critical']):
                        alert_message = f"CRITICAL: {metric.upper()} threshold exceeded for {slice_id} - Current: {value}, Critical: {threshold['critical']}"
                        create_alert_if_not_exists(slice_id, 'CRITICAL', alert_message)
                    
                    # Check for warning alert
                    elif is_warning_alert(metric, value, threshold['warn']):
                        alert_message = f"WARNING: {metric.upper()} threshold exceeded for {slice_id} - Current: {value}, Warning: {threshold['warn']}"
                        create_alert_if_not_exists(slice_id, 'WARN', alert_message)
        
        logger.info("MS-3: Alert generation completed")
        
    except Exception as e:
        logger.error(f"MS-3: Error generating alerts: {str(e)}")

def is_critical_alert(metric, value, critical_threshold):
    """Check if value exceeds critical threshold"""
    if metric in ['bandwidth']:
        return value < critical_threshold  # Lower is worse for bandwidth
    elif metric in ['latency', 'jitter', 'packet_loss']:
        return value > critical_threshold  # Higher is worse for these metrics
    return False

def is_warning_alert(metric, value, warning_threshold):
    """Check if value exceeds warning threshold"""
    if metric in ['bandwidth']:
        return value < warning_threshold  # Lower is worse for bandwidth
    elif metric in ['latency', 'jitter', 'packet_loss']:
        return value > warning_threshold  # Higher is worse for these metrics
    return False

def create_alert_if_not_exists(slice_id, level, message):
    """Create alert only if similar alert doesn't exist in last 5 minutes"""
    try:
        # Check if similar alert exists recently
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        existing_alert = Alert.query.filter(
            Alert.slice_id == slice_id,
            Alert.level == level,
            Alert.message == message,
            Alert.created_at > recent_time
        ).first()
        
        if not existing_alert:
            # Create new alert
            new_alert = Alert(
                slice_id=slice_id,
                level=level,
                message=message,
                acknowledged=False
            )
            db.session.add(new_alert)
            db.session.commit()
            logger.info(f"MS-3: Generated {level} alert for {slice_id}: {message}")
        
    except Exception as e:
        logger.error(f"MS-3: Error creating alert: {str(e)}")

# Database Models for MS-3
class Alert(db.Model):
    """
    Alert Model - Stores network slice alerts
    """
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
    """
    Threshold Model - Stores monitoring thresholds
    """
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

# MS-3 API Routes
@app.route('/ms3/health', methods=['GET'])
def health_check():
    """Health check endpoint for MS-3 service"""
    return jsonify({
        'service': SERVICE_NAME,
        'version': SERVICE_VERSION,
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/dashboard/slices', methods=['GET'])
def get_dashboard_slices():
    """
    MS-3 Endpoint: Get status of all active slices (aggregated from MS-1)
    """
    try:
        logger.info("MS-3: Fetching slice status from MS-1")
        
        # Mock data for MS-1 slices service
        # In real implementation, this would call MS-1 API: http://localhost:5001/slices
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
        
        # Check thresholds and generate alerts automatically
        check_and_generate_alerts(slices_data)
        
        logger.info(f"MS-3: Retrieved {len(slices_data)} active slices")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': slices_data,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"MS-3: Error fetching slices: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alerts', methods=['GET'])
def get_dashboard_alerts():
    """
    MS-3 Endpoint: Get active alerts (WARN/CRITICAL)
    """
    try:
        logger.info("MS-3: Fetching active alerts")
        alerts = Alert.query.filter_by(acknowledged=False).order_by(Alert.created_at.desc()).all()
        
        logger.info(f"MS-3: Retrieved {len(alerts)} active alerts")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': [alert.to_dict() for alert in alerts],
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"MS-3: Error fetching alerts: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/threshold', methods=['POST'])
def configure_threshold():
    """
    MS-3 Endpoint: Configure monitoring thresholds
    """
    try:
        data = request.get_json()
        logger.info(f"MS-3: Configuring threshold for metric: {data.get('metric', 'unknown')}")
        
        if not data or 'metric' not in data:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Missing metric field'}), 400
        
        # Check if threshold already exists
        existing = Threshold.query.filter_by(metric=data['metric']).first()
        if existing:
            existing.warn_value = data.get('warn_value')
            existing.critical_value = data.get('critical_value')
            logger.info(f"MS-3: Updated existing threshold for {data['metric']}")
        else:
            new_threshold = Threshold(
                metric=data['metric'],
                warn_value=data.get('warn_value'),
                critical_value=data.get('critical_value')
            )
            db.session.add(new_threshold)
            logger.info(f"MS-3: Created new threshold for {data['metric']}")
        
        db.session.commit()
        
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'message': 'Threshold configured successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error configuring threshold: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/ack', methods=['POST'])
def acknowledge_alert():
    """
    MS-3 Endpoint: Acknowledge an alert
    """
    try:
        data = request.get_json()
        logger.info(f"MS-3: Acknowledging alert: {data}")
        
        if not data or 'alert_id' not in data:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Missing alert_id field'}), 400
        
        alert = Alert.query.get(data['alert_id'])
        if not alert:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Alert not found'}), 404
        
        alert.acknowledged = True
        db.session.commit()
        
        logger.info(f"MS-3: Alert {alert.id} acknowledged successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'message': 'Alert acknowledged successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error acknowledging alert: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert', methods=['POST'])
def create_alert():
    """
    MS-3 Endpoint: Create a new alert
    """
    try:
        data = request.get_json()
        logger.info(f"MS-3: Creating alert: {data}")
        
        if not data or 'message' not in data:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Missing message field'}), 400
        
        new_alert = Alert(
            slice_id=data.get('slice_id'),
            level=data.get('level', 'WARN'),
            message=data['message'],
            acknowledged=False
        )
        db.session.add(new_alert)
        db.session.commit()
        
        logger.info(f"MS-3: Alert {new_alert.id} created successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': new_alert.to_dict(),
            'message': 'Alert created successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error creating alert: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """
    MS-3 Endpoint: Update an existing alert
    """
    try:
        data = request.get_json()
        logger.info(f"MS-3: Updating alert {alert_id}: {data}")
        
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Alert not found'}), 404
        
        # Update fields
        if 'message' in data:
            alert.message = data['message']
        if 'level' in data:
            alert.level = data['level']
        if 'acknowledged' in data:
            alert.acknowledged = data['acknowledged']
        
        db.session.commit()
        
        logger.info(f"MS-3: Alert {alert_id} updated successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': alert.to_dict(),
            'message': 'Alert updated successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error updating alert: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """
    MS-3 Endpoint: Delete an alert
    """
    try:
        logger.info(f"MS-3: Deleting alert {alert_id}")
        
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        logger.info(f"MS-3: Alert {alert_id} deleted successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'message': 'Alert deleted successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error deleting alert: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/thresholds', methods=['GET'])
def get_thresholds():
    """
    MS-3 Endpoint: Get all configured thresholds
    """
    try:
        logger.info("MS-3: Fetching all thresholds")
        thresholds = Threshold.query.all()
        
        logger.info(f"MS-3: Retrieved {len(thresholds)} thresholds")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': [threshold.to_dict() for threshold in thresholds]
        })
    except Exception as e:
        logger.error(f"MS-3: Error fetching thresholds: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

# Dashboard UI Routes
@app.route('/')
def dashboard():
    """
    MS-3 UI: Main NOC Operator Dashboard
    """
    logger.info("MS-3: Serving dashboard UI")
    return render_template('dashboard.html')

@app.route('/api/qos-history')
def get_qos_history():
    """
    MS-3 Endpoint: Get historical QoS data for charts (aggregated from MS-2)
    """
    try:
        logger.info("MS-3: Fetching QoS historical data from MS-2")
        
        # Mock historical data
        # In real implementation, this would aggregate data from MS-2: http://localhost:5002/qos/history
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
        
        logger.info("MS-3: QoS historical data generated successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': history_data
        })
    except Exception as e:
        logger.error(f"MS-3: Error fetching QoS history: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

# Slice Management Endpoints
@app.route('/dashboard/slice', methods=['POST'])
def create_slice():
    """
    MS-3 Endpoint: Create a new network slice
    """
    try:
        data = request.get_json()
        logger.info(f"MS-3: Creating slice: {data}")
        
        if not data or 'slice_id' not in data:
            return jsonify({'service': 'MS-3', 'status': 'error', 'message': 'Missing slice_id field'}), 400
        
        # For demo, store in memory (in real implementation, would store in database)
        new_slice = {
            'slice_id': data['slice_id'],
            'status': data.get('status', 'ACTIVE'),
            'qos_metrics': data.get('qos_metrics', {
                'bandwidth': 50.0,
                'latency': 10.0,
                'jitter': 1.0,
                'packet_loss': 0.01
            }),
            'ue_count': data.get('ue_count', 0),
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"MS-3: Slice {data['slice_id']} created successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'data': new_slice,
            'message': 'Slice created successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error creating slice: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/slice/<string:slice_id>', methods=['PUT'])
def update_slice(slice_id):
    """
    MS-3 Endpoint: Update an existing network slice
    """
    try:
        data = request.get_json()
        logger.info(f"MS-3: Updating slice {slice_id}: {data}")
        
        # For demo, return success (in real implementation, would update database)
        logger.info(f"MS-3: Slice {slice_id} updated successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'message': 'Slice updated successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error updating slice: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/slice/<string:slice_id>', methods=['DELETE'])
def delete_slice(slice_id):
    """
    MS-3 Endpoint: Delete a network slice
    """
    try:
        logger.info(f"MS-3: Deleting slice {slice_id}")
        
        # For demo, return success (in real implementation, would delete from database)
        logger.info(f"MS-3: Slice {slice_id} deleted successfully")
        return jsonify({
            'service': 'MS-3',
            'status': 'success',
            'message': 'Slice deleted successfully'
        })
    except Exception as e:
        logger.error(f"MS-3: Error deleting slice: {str(e)}")
        return jsonify({'service': 'MS-3', 'status': 'error', 'message': str(e)}), 500

# Initialize database for MS-3
def create_tables():
    """
    MS-3: Initialize database tables and default data
    """
    logger.info("MS-3: Initializing database")
    with app.app_context():
        db.create_all()
        
        # Initialize default thresholds if none exist
        if Threshold.query.count() == 0:
            logger.info("MS-3: Creating default thresholds")
            default_thresholds = [
                Threshold(metric='bandwidth', warn_value=70.0, critical_value=50.0),
                Threshold(metric='latency', warn_value=20.0, critical_value=50.0),
                Threshold(metric='packet_loss', warn_value=0.02, critical_value=0.05),
                Threshold(metric='jitter', warn_value=3.0, critical_value=5.0)
            ]
            for threshold in default_thresholds:
                db.session.add(threshold)
            db.session.commit()
            logger.info("MS-3: Default thresholds created successfully")

# Initialize database on startup
create_tables()

# MS-3 Service Entry Point
if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION} on port {SERVICE_PORT}")
    logger.info("MS-3: Dashboard & Alerts Service ready")
    app.run(debug=True, host='0.0.0.0', port=SERVICE_PORT)
