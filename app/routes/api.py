from flask import Blueprint, request, jsonify
from app import db
from app.models import Anomaly
from datetime import datetime, timedelta
from sqlalchemy import func
import logging
import json

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

_detection_service = None


def get_detection_service():
    """Initialiser le service de detection uniquement quand l'API en a besoin."""
    global _detection_service
    if _detection_service is None:
        from app.services.consensus_service import ConsensusAnomalyDetectionService
        _detection_service = ConsensusAnomalyDetectionService()
    return _detection_service


@api_bp.route('/anomaly/detect', methods=['POST'])
def detect_anomaly():
    """
    POST /anomaly/detect
    
    Détecter une anomalie en analysant les features fournies
    
    Request JSON:
    {
        "slice_id": "slice_001",
        "features": {
            "bandwidth": 85.5,
            "latency": 12.3,
            "jitter": 2.1,
            "packet_loss": 1.0
        }
    }
    
    Response:
    {
        "success": true,
        "data": {
            "is_anomaly": false,
            "score": 0.3421,
            "confidence": 0.6579,
            "method": "isolation_forest",
            "methods": {...},
            "anomaly_id": 123
        }
    }
    """
    try:
        data = request.get_json()
        
        # Validation
        if not data or 'features' not in data:
            return jsonify({
                'success': False,
                'error': 'Manquant: "features" requis'
            }), 400
        
        slice_id = data.get('slice_id', 'unknown')
        features = data.get('features')
        
        # Détection d'anomalie
        detection_result = get_detection_service().detect(features)
        
        # Sauvegarder dans la BDD
        anomaly = Anomaly(
            slice_id=slice_id,
            score=detection_result['score'],
            is_anomaly=detection_result['is_anomaly'],
            method=detection_result['method'],
            isolation_forest_score=detection_result['methods']['isolation_forest']['score'],
            autoencoder_score=detection_result['methods']['autoencoder']['score'],
            features_json=json.dumps(features)
        )
        
        db.session.add(anomaly)
        db.session.commit()
        
        detection_result['anomaly_id'] = anomaly.id
        
        logger.info(f"Anomalie détectée pour {slice_id}: {detection_result['is_anomaly']}")
        
        return jsonify({
            'success': True,
            'data': detection_result
        }), 201
    
    except Exception as e:
        logger.error(f"Erreur dans /anomaly/detect: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/anomaly/history', methods=['GET'])
def get_anomaly_history():
    """
    GET /anomaly/history
    
    Retourner l'historique des anomalies détectées
    
    Query Parameters:
    - slice_id: filtrer par slice_id (optionnel)
    - is_anomaly: filtrer par is_anomaly (true/false, optionnel)
    - method: filtrer par méthode (optionnel)
    - start_date: date de début (format: YYYY-MM-DD HH:MM:SS, optionnel)
    - end_date: date de fin (format: YYYY-MM-DD HH:MM:SS, optionnel)
    - limit: nombre maximum de résultats (défaut: 100)
    - offset: décalage pour la pagination (défaut: 0)
    
    Response:
    {
        "success": true,
        "data": {
            "total": 150,
            "count": 10,
            "anomalies": [...]
        }
    }
    """
    try:
        # Paramètres de requête
        slice_id = request.args.get('slice_id', None)
        is_anomaly = request.args.get('is_anomaly', None)
        method = request.args.get('method', None)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validation des limites
        limit = min(limit, 500)
        if limit < 1:
            limit = 100
        
        # Construire la requête
        query = Anomaly.query
        
        if slice_id:
            query = query.filter_by(slice_id=slice_id)
        
        if is_anomaly is not None:
            is_anomaly_bool = is_anomaly.lower() in ['true', '1', 'yes']
            query = query.filter_by(is_anomaly=is_anomaly_bool)
        
        if method:
            query = query.filter_by(method=method)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
                query = query.filter(Anomaly.created_at >= start)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Format de date invalide pour start_date: {start_date}'
                }), 400
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
                query = query.filter(Anomaly.created_at <= end)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Format de date invalide pour end_date: {end_date}'
                }), 400
        
        # Compter le total
        total = query.count()
        
        # Appliquer pagination
        anomalies = query.order_by(Anomaly.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'count': len(anomalies),
                'anomalies': [a.to_dict() for a in anomalies]
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur dans /anomaly/history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/anomaly/stats', methods=['GET'])
def get_anomaly_stats():
    """
    GET /anomaly/stats
    
    Retourner les statistiques d'anomalies par période
    
    Query Parameters:
    - slice_id: filtrer par slice_id (optionnel)
    - period: jour/semaine/mois (défaut: jour)
    - days: nombre de jours à inclure (défaut: 7)
    
    Response:
    {
        "success": true,
        "data": {
            "total_anomalies": 15,
            "anomaly_rate": 0.15,
            "by_slice": {...},
            "by_period": [...],
            "by_method": {...}
        }
    }
    """
    try:
        slice_id = request.args.get('slice_id', None)
        period = request.args.get('period', 'jour').lower()
        days = request.args.get('days', 7, type=int)
        
        # Déterminer la date de début
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Requête principale
        query = Anomaly.query.filter(Anomaly.created_at >= start_date)
        
        if slice_id:
            query = query.filter_by(slice_id=slice_id)
        
        all_anomalies = query.all()
        detected_anomalies = [a for a in all_anomalies if a.is_anomaly]
        
        # Stats globales
        total = len(all_anomalies)
        total_anomalies = len(detected_anomalies)
        anomaly_rate = (total_anomalies / total * 100) if total > 0 else 0
        
        # Stats par slice_id
        by_slice = {}
        for anomaly in all_anomalies:
            sid = anomaly.slice_id or 'unknown'
            if sid not in by_slice:
                by_slice[sid] = {'total': 0, 'anomalies': 0, 'rate': 0}
            by_slice[sid]['total'] += 1
            if anomaly.is_anomaly:
                by_slice[sid]['anomalies'] += 1
        
        for sid in by_slice:
            total_sid = by_slice[sid]['total']
            anom_sid = by_slice[sid]['anomalies']
            by_slice[sid]['rate'] = round((anom_sid / total_sid * 100) if total_sid > 0 else 0, 2)
        
        # Stats par méthode
        by_method = {}
        for anomaly in detected_anomalies:
            method = anomaly.method or 'unknown'
            if method not in by_method:
                by_method[method] = 0
            by_method[method] += 1
        
        # Stats par période (grouper par date)
        by_period = {}
        for anomaly in all_anomalies:
            date_key = anomaly.created_at.strftime('%Y-%m-%d')
            if date_key not in by_period:
                by_period[date_key] = {'total': 0, 'anomalies': 0}
            by_period[date_key]['total'] += 1
            if anomaly.is_anomaly:
                by_period[date_key]['anomalies'] += 1
        
        # Convertir to list et trier
        by_period_list = []
        for date_key in sorted(by_period.keys()):
            rate = (by_period[date_key]['anomalies'] / by_period[date_key]['total'] * 100) \
                if by_period[date_key]['total'] > 0 else 0
            by_period_list.append({
                'date': date_key,
                'total': by_period[date_key]['total'],
                'anomalies': by_period[date_key]['anomalies'],
                'rate': round(rate, 2)
            })
        
        return jsonify({
            'success': True,
            'data': {
                'total_detections': total,
                'total_anomalies': total_anomalies,
                'anomaly_rate': round(anomaly_rate, 2),
                'by_slice': by_slice,
                'by_method': by_method,
                'by_period': by_period_list,
                'period': period,
                'days': days
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur dans /anomaly/stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
