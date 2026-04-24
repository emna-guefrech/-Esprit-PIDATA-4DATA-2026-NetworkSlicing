"""
Dashboard blueprint - main dashboard view and APIs
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.models.monitoring import Alert, Threshold, Prediction, Anomaly
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
@login_required
def index():
    """
    Main dashboard page
    Shows overview cards and monitoring data
    """
    # Fetch data for dashboard
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(10).all()
    thresholds = Threshold.query.all()
    predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(5).all()
    
    # Count alerts by level
    critical_alerts = Alert.query.filter_by(level='CRITICAL').count()
    warning_alerts = Alert.query.filter_by(level='WARN').count()
    
    # Count unacknowledged alerts
    unacknowledged_alerts = Alert.query.filter_by(acknowledged=False).count()
    
    # Count active predictions
    active_predictions = Prediction.query.count()
    
    # Prepare context
    context = {
        'user': current_user,
        'alerts': alerts,
        'thresholds': thresholds,
        'predictions': predictions,
        'now': datetime.utcnow(),
        'stats': {
            'critical_alerts': critical_alerts,
            'warning_alerts': warning_alerts,
            'unacknowledged_alerts': unacknowledged_alerts,
            'active_predictions': active_predictions,
            'active_slices': len(set(p.slice_id for p in predictions)) if predictions else 0,
        }
    }
    
    return render_template('dashboard/index.html', **context)


@dashboard_bp.route('/api/dashboard/metrics', methods=['GET'])
@login_required
def api_metrics():
    """
    API endpoint for dashboard metrics
    Returns JSON for AJAX updates
    """
    alerts_count = Alert.query.count()
    critical_alerts = Alert.query.filter_by(level='CRITICAL').count()
    predictions_count = Prediction.query.count()
    
    return jsonify({
        'status': 'success',
        'data': {
            'total_alerts': alerts_count,
            'critical_alerts': critical_alerts,
            'total_predictions': predictions_count,
            'timestamp': datetime.utcnow().isoformat(),
        }
    })
