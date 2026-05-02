#!/usr/bin/env python
"""
Anomaly Detection Service - MS-2
Microservice Flask pour la détection d'anomalies en temps réel
"""

import os
from dotenv import load_dotenv
from app import create_app, db

# Charger les variables d'environnement
load_dotenv()

# Créer l'application Flask
app = create_app(os.environ.get('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    """Contexte pour flask shell"""
    return {
        'db': db,
        'app': app
    }

@app.before_request
def setup():
    """Vérifier la connexion DB"""
    try:
        db.session.execute('SELECT 1')
    except Exception as e:
        app.logger.warning(f"Database check failed: {e}")

if __name__ == '__main__':
    # Configuration du serveur
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║  Anomaly Detection Service - MS-2                             ║
    ║  Flask Application Starting...                                ║
    ╠════════════════════════════════════════════════════════════════╣
    ║  Host: {host:<51}║
    ║  Port: {port:<51}║
    ║  Debug: {str(debug_mode):<50}║
    ║  Environment: {os.environ.get('FLASK_ENV', 'development'):<44}║
    ╠════════════════════════════════════════════════════════════════╣
    ║  Dashboard:     http://{host}:{port}                            ║
    ║  API Docs:      http://{host}:{port}/api/anomaly/detect       ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=debug_mode
    )
