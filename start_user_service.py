#!/usr/bin/env python3
"""
Script de démarrage pour le service User
Port: 5000
Base de données: network_slicing_
"""

import os
import sys

# Ajouter le répertoire user/flask au path Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'user', 'flask'))

try:
    # Importer l'application User
    from app import create_app
    
    if __name__ == '__main__':
        print("🚀 Démarrage du service User (Port 5000)...")
        print("📍 URL: http://localhost:5000/")
        print("👥 Service de gestion des utilisateurs")
        print("🗄️ Base de données: network_slicing_")
        print("=" * 50)
        
        # Créer l'application
        app = create_app('development')
        
        # Démarrer sur le port 5000
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
        
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("📋 Assurez-vous que le fichier app.py existe dans user/flask/")
    print("🔧 Vérifiez que toutes les dépendances sont installées")
except Exception as e:
    print(f"❌ Erreur au démarrage: {e}")
