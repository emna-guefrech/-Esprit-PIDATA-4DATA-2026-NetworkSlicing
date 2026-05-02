# MS-3 NOC Dashboard & Alerts Service

## 🎯 Rôle
Dashboard pour opérateurs NOC - Agrégation des données de MS-1 et MS-2

## 📁 Structure
- `app.py` - Application Flask principale
- `models.py` - Modèles Alert et Threshold
- `dashboard.html` - Interface web
- `service.py` - Service complet avec tous les endpoints
- `run.py` - Lanceur du service
- `requirements.txt` - Dépendances

## 🚀 Lancement
```bash
cd ms3
pip install -r requirements.txt
python app.py
```

## 🌐 Accès
- Dashboard: http://localhost:5003
- API: http://localhost:5003/dashboard/*

## 📡 Endpoints
- `GET /dashboard/slices` - État des slices actives
- `GET /dashboard/alerts` - Alertes actives
- `POST /dashboard/threshold` - Configurer seuils
- `POST /dashboard/alert/ack` - Acknowledger alerte

## 🔗 Intégration
- Appelle MS-1 (port 5001) pour les prédictions QoS
- Appelle MS-2 (port 5002) pour la détection d'anomalies
- Base de données MySQL partagée
