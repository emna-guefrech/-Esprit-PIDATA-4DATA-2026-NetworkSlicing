# Anomaly Detection Service - MS-2

## Overview
Microservice Flask complet pour la détection d'anomalies en temps réel dans le système de **Network Slicing**. Utilise un consensus entre **Isolation Forest** et **Autoencoder** pour optimiser la détection.

## Architecture

```
anomalies/
├── app/
│   ├── __init__.py              # Application Factory
│   ├── models/
│   │   ├── __init__.py
│   │   └── anomaly.py           # Modèle SQLAlchemy pour les anomalies
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py               # Routes API (3 endpoints)
│   │   └── web.py               # Routes Web (Dashboard)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── isolation_forest_service.py  # Service Isolation Forest
│   │   ├── autoencoder_service.py       # Service Autoencoder
│   │   └── consensus_service.py         # Service Consensus
│   ├── templates/
│   │   ├── base.html            # Template de base
│   │   ├── index.html           # Dashboard principal
│   │   ├── history.html         # Historique des anomalies
│   │   └── stats.html           # Statistiques
│   └── static/
│       ├── css/
│       │   └── style.css        # Styles (thème Network Slicing)
│       └── js/
│           ├── utils.js         # Utilitaires globaux
│           ├── dashboard.js     # Logique Dashboard
│           ├── history.js       # Logique Historique
│           └── stats.js         # Logique Statistiques
├── config.py                    # Configuration Flask
├── run.py                       # Point d'entrée de l'application
├── requirements.txt             # Dépendances Python
├── .env                         # Variables d'environnement
└── README.md                    # Ce fichier
```

## Installation

### Prérequis
- Python 3.8+
- MySQL 8.0+
- pip

### Étapes

1. **Cloner/Créer le projet**
```bash
cd c:\Users\MSI\Desktop\4eme Data\PI data\anomalies
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Créer la base de données MySQL**
```bash
mysql -u root < network_slicing.sql
```

5. **Configurer les variables d'environnement**
- Éditer `.env` avec vos paramètres de connexion MySQL
- Par défaut: `mysql://root:@localhost:3306/network_slicing`

6. **Lancer l'application**
```bash
python run.py
```

L'application sera disponible à: **http://localhost:5000**

## API Endpoints

### 1. POST /api/anomaly/detect
Détecter une anomalie en analysant les features fournies.

**Request:**
```json
{
  "slice_id": "slice_001",
  "features": {
    "bandwidth": 85.5,
    "latency": 12.3,
    "jitter": 2.1,
    "packet_loss": 1.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "is_anomaly": false,
    "score": 0.3421,
    "confidence": 0.6579,
    "method": "isolation_forest",
    "anomaly_id": 123,
    "methods": {
      "isolation_forest": {
        "is_anomaly": false,
        "score": 0.3412
      },
      "autoencoder": {
        "is_anomaly": false,
        "score": 0.3430
      }
    }
  }
}
```

### 2. GET /api/anomaly/history
Retourner l'historique des anomalies détectées avec filtres.

**Query Parameters:**
- `slice_id`: Filtrer par slice_id
- `is_anomaly`: Filtrer par type (true/false)
- `method`: Filtrer par méthode (isolation_forest/autoencoder)
- `start_date`: Date de début (format: YYYY-MM-DD HH:MM:SS)
- `end_date`: Date de fin
- `limit`: Nombre max de résultats (défaut: 100, max: 500)
- `offset`: Décalage pour pagination (défaut: 0)

**Example:**
```
GET /api/anomaly/history?slice_id=slice_001&is_anomaly=true&limit=50&offset=0
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 150,
    "count": 10,
    "anomalies": [
      {
        "id": 1,
        "slice_id": "slice_001",
        "score": 0.8234,
        "is_anomaly": true,
        "method": "isolation_forest",
        "confidence_level": "HIGH",
        "isolation_forest_score": 0.8234,
        "autoencoder_score": 0.8126,
        "created_at": "2026-04-25T10:30:00"
      }
    ]
  }
}
```

### 3. GET /api/anomaly/stats
Retourner les statistiques d'anomalies par période.

**Query Parameters:**
- `slice_id`: Filtrer par slice_id (optionnel)
- `period`: jour/semaine/mois (défaut: jour)
- `days`: Nombre de jours à inclure (défaut: 7)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_detections": 500,
    "total_anomalies": 45,
    "anomaly_rate": 9.0,
    "by_slice": {
      "slice_001": {
        "total": 200,
        "anomalies": 15,
        "rate": 7.5
      }
    },
    "by_method": {
      "isolation_forest": 30,
      "autoencoder": 15
    },
    "by_period": [
      {
        "date": "2026-04-24",
        "total": 100,
        "anomalies": 8,
        "rate": 8.0
      }
    ]
  }
}
```

## Frontend Routes

- `/` - Dashboard principal
- `/history` - Historique des anomalies
- `/stats` - Statistiques

## Modèles ML

### Isolation Forest
- **Contamination**: 5% (proportion d'anomalies supposée)
- **Algorithme**: Isolation basée sur les partitions aléatoires
- **Avantages**: Rapide, pas de normalisation requise, bon pour les anomalies globales

### Autoencoder
- **Architecture**: 
  - Input → Dense(64) → Dense(32) → Dense(8) [Encoding]
  - Dense(32) → Dense(64) → Output
- **Seuil**: 95e percentile de l'erreur de reconstruction
- **Avantages**: Détecte les patterns complexes, bon pour les anomalies contextuelles

### Consensus
- **Logique**: Détection confirmée si **les 2 modèles** la signalent
- **Score**: Moyenne des scores IF + AE
- **Confiance**: Score si anomalie, sinon 1 - score

## Database Schema

Table `anomalies`:
```sql
- id INT PRIMARY KEY AUTO_INCREMENT
- slice_id VARCHAR(50) INDEX
- score FLOAT
- is_anomaly BOOLEAN
- method VARCHAR(30)
- isolation_forest_score FLOAT
- autoencoder_score FLOAT
- features_json TEXT
- created_at DATETIME INDEX DEFAULT NOW()
```

## Configuration

Éditer `.env` pour modifier:

```bash
# Server
FLASK_ENV=development          # development/production
FLASK_DEBUG=True              # Debug mode
FLASK_PORT=5000               # Port

# Database
DATABASE_URL=mysql+pymysql://root:@localhost:3306/network_slicing

# ML Models
CONTAMINATION_RATE=0.05       # Isolation Forest contamination
AUTOENCODER_ENCODING_DIM=8    # Autoencoder encoding dimension
```

## Usage Example

### Via Python (Direct API)
```python
from app import create_app
from app.services import ConsensusAnomalyDetectionService

app = create_app()
service = ConsensusAnomalyDetectionService()

features = {
    'bandwidth': 85.5,
    'latency': 12.3,
    'jitter': 2.1,
    'packet_loss': 1.0
}

result = service.detect(features)
print(result)
```

### Via cURL (HTTP API)
```bash
curl -X POST http://localhost:5000/api/anomaly/detect \
  -H "Content-Type: application/json" \
  -d '{
    "slice_id": "slice_001",
    "features": {
      "bandwidth": 85.5,
      "latency": 12.3,
      "jitter": 2.1,
      "packet_loss": 1.0
    }
  }'
```

### Via Python Requests
```python
import requests

response = requests.post(
    'http://localhost:5000/api/anomaly/detect',
    json={
        'slice_id': 'slice_001',
        'features': {
            'bandwidth': 85.5,
            'latency': 12.3,
            'jitter': 2.1,
            'packet_loss': 1.0
        }
    }
)

print(response.json())
```

## Dashboard Features

✅ **Détection en temps réel**: Affichage des slices actifs avec statut  
✅ **Alertes actives**: Liste des anomalies détectées  
✅ **Seuils configurables**: Affichage des thresholds par métrique  
✅ **Historique complet**: Recherche et filtrage avancé  
✅ **Statistiques**: Graphiques de tendances par période  
✅ **Responsive**: Adaptation mobile/desktop  

## Performance

- **Détection**: < 100ms par anomalie
- **Stockage**: ~2KB par détection (avec features JSON)
- **Base de données**: Indexation sur slice_id et created_at
- **Refresh dashboard**: 10 secondes (configurable)

## Troubleshooting

### Erreur de connexion MySQL
```bash
# Vérifier que MySQL est lancé
mysql -u root -p

# Vérifier la configuration DATABASE_URL dans .env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/network_slicing
```

### Modèles ML non entraînés
Au premier démarrage, les modèles vont utiliser des valeurs par défaut. Pour améliorer les résultats:
1. Collecter un dataset historique
2. Entraîner les modèles: `python -c "from app.services import ConsensusAnomalyDetectionService; service = ConsensusAnomalyDetectionService()"`

### Port 5000 déjà utilisé
Modifier dans `.env`:
```bash
FLASK_PORT=5001
```

## Architecture Système Complet

```
┌─────────────────────────────────────────────────────┐
│  Network Slicing Platform                           │
├─────────────────────────────────────────────────────┤
│  MS-1: Network Slicing Manager                      │
│  MS-2: Anomaly Detection Service (THIS)             │
│  MS-3: Network Slicing Dashboard                    │
│  MS-4: Data Analytics Service                       │
└─────────────────────────────────────────────────────┘
         ↓
    ┌─────────────┐
    │  MySQL BDD  │
    │  - anomalies│
    │  - thresholds│
    │  - users    │
    └─────────────┘
```

## Licensing & Notes

- **Développement**: 2026
- **Framework**: Flask 2.3+
- **ML**: scikit-learn 1.2+, TensorFlow 2.12+
- **Database**: MySQL 8.0+

---

**MS-2 Anomaly Detection Service** - Real-time Anomaly Detection for Network Slicing Platform
