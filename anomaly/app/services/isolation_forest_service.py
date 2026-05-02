import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os
import logging

logger = logging.getLogger(__name__)


class IsolationForestService:
    """Service de détection d'anomalies avec Isolation Forest"""
    
    def __init__(self, contamination=0.05):
        """
        Initialiser le modèle Isolation Forest
        
        Args:
            contamination: proportion d'anomalies supposée dans les données (0 à 1)
        """
        self.contamination = contamination
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.model_path = 'models/isolation_forest_model.pkl'
        self.scaler_path = 'models/isolation_forest_scaler.pkl'
        
        self._load_model()
    
    def _load_model(self):
        """Charger le modèle préalablement entraîné"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_trained = True
                logger.info("Modèle Isolation Forest chargé")
        except Exception as e:
            logger.warning(f"Impossible de charger le modèle Isolation Forest: {e}")
            self.model = IsolationForest(contamination=self.contamination, random_state=42)
            self.scaler = StandardScaler()
    
    def train(self, X_train):
        """
        Entraîner le modèle Isolation Forest
        
        Args:
            X_train: données d'entraînement (numpy array ou liste de listes)
        
        Returns:
            self
        """
        X_train = np.array(X_train)
        
        # Normalisation
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Entraînement
        self.model.fit(X_scaled)
        self.is_trained = True
        
        # Sauvegarder le modèle
        os.makedirs('models', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        with open(self.scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        logger.info("Modèle Isolation Forest entraîné et sauvegardé")
        return self
    
    def predict(self, X):
        """
        Prédire les anomalies
        
        Args:
            X: données à prédire (numpy array ou liste)
        
        Returns:
            tuple: (predictions [-1 ou 1], anomaly_scores, probabilities)
        """
        if not self.is_trained:
            # Si pas entraîné, retourner des scores neutres
            logger.warning("Modèle Isolation Forest non entraîné")
            X = np.array(X).reshape(1, -1) if not isinstance(X, np.ndarray) else X
            return np.ones(len(X)), np.zeros(len(X)), np.full(len(X), 0.5)
        
        X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Normalisation
        X_scaled = self.scaler.transform(X)
        
        # Prédictions (-1 pour anomalie, 1 pour normal)
        predictions = self.model.predict(X_scaled)
        
        # Scores d'anomalie (plus proche de -1 = plus anomalique)
        anomaly_scores = -self.model.score_samples(X_scaled)
        
        # Normaliser les scores entre 0 et 1
        min_score = anomaly_scores.min()
        max_score = anomaly_scores.max()
        if max_score > min_score:
            probabilities = (anomaly_scores - min_score) / (max_score - min_score)
        else:
            probabilities = np.full(len(anomaly_scores), 0.5)
        
        return predictions, anomaly_scores, probabilities
    
    def predict_single(self, features):
        """
        Prédire une anomalie unique
        
        Args:
            features: liste ou dict de features
        
        Returns:
            dict: {'is_anomaly': bool, 'score': float}
        """
        if isinstance(features, dict):
            features = list(features.values())
        
        predictions, _, probabilities = self.predict([features])
        
        is_anomaly = predictions[0] == -1
        score = probabilities[0]
        
        return {
            'is_anomaly': bool(is_anomaly),
            'score': float(score)
        }
