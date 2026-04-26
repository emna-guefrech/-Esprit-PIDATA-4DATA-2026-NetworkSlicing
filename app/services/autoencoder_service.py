import numpy as np
import os
import logging
import json

try:
    from tensorflow import keras
    from tensorflow.keras import layers
except ModuleNotFoundError:
    keras = None
    layers = None

logger = logging.getLogger(__name__)


class AutoencoderService:
    """Service de détection d'anomalies avec Autoencoder"""
    
    def __init__(self, input_dim=None, encoding_dim=8, threshold=0.5):
        """
        Initialiser l'Autoencoder
        
        Args:
            input_dim: dimension de l'input
            encoding_dim: dimension de l'encoding layer
            threshold: seuil de reconstruction error pour détecter anomalie
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.threshold = threshold
        self.model = None
        self.is_trained = False
        self.model_path = 'models/autoencoder_model.h5'
        self.threshold_path = 'models/autoencoder_threshold.json'
        
        self._load_model()
    
    def _load_model(self):
        """Charger le modèle préalablement entraîné"""
        if keras is None:
            logger.warning("TensorFlow n'est pas installe; Autoencoder desactive")
            return

        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                self.input_dim = self.model.input_shape[1]
                self.is_trained = True
                
                # Charger le seuil
                try:
                    with open(self.threshold_path, 'r') as f:
                        data = json.load(f)
                        self.threshold = data.get('threshold', 0.5)
                except:
                    pass
                
                logger.info("Modèle Autoencoder chargé")
        except Exception as e:
            logger.warning(f"Impossible de charger le modèle Autoencoder: {e}")
    
    def build(self, input_dim):
        """
        Construire le modèle Autoencoder
        
        Args:
            input_dim: dimension de l'input
        
        Returns:
            self
        """
        self.input_dim = input_dim

        if keras is None or layers is None:
            raise RuntimeError("TensorFlow doit etre installe pour construire l'Autoencoder")
        
        # Encoder
        input_img = keras.Input(shape=(input_dim,))
        encoded = layers.Dense(64, activation='relu')(input_img)
        encoded = layers.Dense(32, activation='relu')(encoded)
        encoded = layers.Dense(self.encoding_dim, activation='relu')(encoded)
        
        # Decoder
        decoded = layers.Dense(32, activation='relu')(encoded)
        decoded = layers.Dense(64, activation='relu')(decoded)
        decoded = layers.Dense(input_dim, activation='linear')(decoded)
        
        # Autoencoder complet
        self.model = keras.Model(input_img, decoded)
        self.model.compile(optimizer='adam', loss='mse')
        
        logger.info(f"Modèle Autoencoder construit (input_dim={input_dim}, encoding_dim={self.encoding_dim})")
        return self
    
    def train(self, X_train, epochs=50, batch_size=32, validation_split=0.2):
        """
        Entraîner l'Autoencoder
        
        Args:
            X_train: données d'entraînement
            epochs: nombre d'époques
            batch_size: taille des batches
            validation_split: proportion de données de validation
        
        Returns:
            self
        """
        if self.model is None:
            raise ValueError("Le modèle doit être construit avant d'entraîner")
        
        X_train = np.array(X_train)
        
        # Entraînement
        history = self.model.fit(
            X_train, X_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
        # Calculer les reconstruction errors
        train_predictions = self.model.predict(X_train)
        mse = np.mean(np.power(X_train - train_predictions, 2), axis=1)
        
        # Définir le seuil (95e percentile)
        self.threshold = np.percentile(mse, 95)
        
        # Sauvegarder le modèle
        os.makedirs('models', exist_ok=True)
        self.model.save(self.model_path)
        
        # Sauvegarder le seuil
        with open(self.threshold_path, 'w') as f:
            json.dump({'threshold': float(self.threshold)}, f)
        
        self.is_trained = True
        logger.info(f"Modèle Autoencoder entraîné. Seuil: {self.threshold:.4f}")
        return self
    
    def predict(self, X):
        """
        Prédire les anomalies avec l'Autoencoder
        
        Args:
            X: données à prédire
        
        Returns:
            tuple: (predictions [-1 ou 1], reconstruction_errors, probabilities)
        """
        if self.model is None:
            logger.warning("Modèle Autoencoder non entraîné")
            X = np.array(X)
            if X.ndim == 1:
                X = X.reshape(1, -1)
            return np.ones(len(X)), np.zeros(len(X)), np.full(len(X), 0.5)
        
        X = np.array(X)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # Prédictions
        X_pred = self.model.predict(X, verbose=0)
        
        # Reconstruction error (MSE par sample)
        mse = np.mean(np.power(X - X_pred, 2), axis=1)
        
        # Prédictions (-1 pour anomalie, 1 pour normal)
        predictions = np.where(mse > self.threshold, -1, 1)
        
        # Normaliser les scores entre 0 et 1
        probabilities = 1 / (1 + np.exp(-10 * (mse - self.threshold)))
        
        return predictions, mse, probabilities
    
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
        
        predictions, mse, probabilities = self.predict([features])
        
        is_anomaly = predictions[0] == -1
        score = probabilities[0]
        
        return {
            'is_anomaly': bool(is_anomaly),
            'score': float(score)
        }
