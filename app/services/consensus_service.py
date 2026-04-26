import logging
from app.services.isolation_forest_service import IsolationForestService
from app.services.autoencoder_service import AutoencoderService

logger = logging.getLogger(__name__)


class ConsensusAnomalyDetectionService:
    """Service de détection d'anomalies par consensus (Isolation Forest + Autoencoder)"""
    
    def __init__(self):
        """Initialiser le service de détection"""
        self.isolation_forest = IsolationForestService(contamination=0.05)
        self.autoencoder = AutoencoderService(encoding_dim=8)
    
    def detect(self, features):
        """
        Détecter une anomalie avec consensus
        
        Args:
            features: dict ou list de features
        
        Returns:
            dict: {
                'is_anomaly': bool,
                'score': float (moyenne des deux scores),
                'confidence': float (0 à 1),
                'methods': {
                    'isolation_forest': {'is_anomaly': bool, 'score': float},
                    'autoencoder': {'is_anomaly': bool, 'score': float}
                }
            }
        """
        # Détection avec Isolation Forest
        if_result = self.isolation_forest.predict_single(features)
        
        # Détection avec Autoencoder
        ae_result = self.autoencoder.predict_single(features)
        
        # Consensus
        if_anomaly = if_result['is_anomaly']
        ae_anomaly = ae_result['is_anomaly']
        
        # Une anomalie est confirmée si les deux modèles l'indiquent (consensus strict)
        # Ou si on peut utiliser un vote (au moins 1 des 2)
        is_anomaly = if_anomaly and ae_anomaly  # Consensus strict
        
        # Score final = moyenne des scores
        score = (if_result['score'] + ae_result['score']) / 2
        
        # Confiance = moyenne des scores si anomalie, sinon 1 - moyenne
        confidence = score if is_anomaly else 1 - score
        
        # Méthode de détection (celui qui a le score le plus haut)
        if if_result['score'] > ae_result['score']:
            method = 'isolation_forest'
        else:
            method = 'autoencoder'
        
        result = {
            'is_anomaly': is_anomaly,
            'score': round(score, 4),
            'confidence': round(confidence, 4),
            'method': method,
            'methods': {
                'isolation_forest': {
                    'is_anomaly': if_anomaly,
                    'score': round(if_result['score'], 4)
                },
                'autoencoder': {
                    'is_anomaly': ae_anomaly,
                    'score': round(ae_result['score'], 4)
                }
            }
        }
        
        logger.info(f"Détection anomalie: {result}")
        return result
    
    def detect_batch(self, features_list):
        """
        Détecter des anomalies en batch
        
        Args:
            features_list: liste de dicts ou lists de features
        
        Returns:
            list: liste de résultats de détection
        """
        results = []
        for features in features_list:
            results.append(self.detect(features))
        return results
