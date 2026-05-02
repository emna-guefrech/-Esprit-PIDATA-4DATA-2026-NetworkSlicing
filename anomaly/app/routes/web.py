from flask import Blueprint, render_template, jsonify
from app import db
from app.models import Anomaly
from datetime import datetime, timedelta
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Page d'accueil - Dashboard des anomalies"""
    return render_template('index.html')


@web_bp.route('/history')
def history():
    """Page historique des anomalies"""
    return render_template('history.html')


@web_bp.route('/stats')
def stats():
    """Page statistiques"""
    return render_template('stats.html')


@web_bp.route('/api/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Récupérer les données du dashboard"""
    try:
        # Dernières 24 heures
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        # Stats dernières 24h
        recent_anomalies = Anomaly.query.filter(
            Anomaly.created_at >= last_24h,
            Anomaly.is_anomaly == True
        ).all()
        
        # Stats par slice_id
        slices_stats = db.session.query(
            Anomaly.slice_id,
            func.count(Anomaly.id).label('total'),
            func.sum(Anomaly.is_anomaly).label('anomalies')
        ).filter(
            Anomaly.created_at >= last_24h
        ).group_by(Anomaly.slice_id).all()
        
        slices_data = []
        for slice_id, total, anomalies in slices_stats:
            anomalies_count = anomalies or 0
            status = 'ACTIVE' if anomalies_count == 0 else 'DEGRADED'
            
            # Récupérer les metrics du dernier enregistrement
            latest = Anomaly.query.filter_by(slice_id=slice_id).order_by(
                Anomaly.created_at.desc()
            ).first()
            
            if latest and latest.features_json:
                import json
                try:
                    features = json.loads(latest.features_json)
                except:
                    features = {}
            else:
                features = {}
            
            slices_data.append({
                'slice_id': slice_id,
                'status': status,
                'total_detections': total,
                'anomalies': anomalies_count,
                'bandwidth': features.get('bandwidth', 0),
                'latency': features.get('latency', 0),
                'jitter': features.get('jitter', 0),
                'packet_loss': features.get('packet_loss', 0),
                'anomaly_rate': round((anomalies_count / total * 100) if total > 0 else 0, 2)
            })
        
        # Alerts
        alerts = []
        for slice_data in slices_data:
            if slice_data['status'] == 'DEGRADED':
                alerts.append({
                    'level': 'WARN',
                    'message': f"Anomalies détectées pour {slice_data['slice_id']}",
                    'slice_id': slice_data['slice_id']
                })
        
        return jsonify({
            'success': True,
            'data': {
                'recent_anomalies': len(recent_anomalies),
                'active_alerts': len(alerts),
                'slices': slices_data,
                'alerts': alerts,
                'last_updated': datetime.utcnow().isoformat()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur dans /api/dashboard-data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
