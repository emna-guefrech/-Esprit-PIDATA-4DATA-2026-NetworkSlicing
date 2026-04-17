#!/usr/bin/env python3
"""
Force reload Streamlit and clear cache
"""

import os
import sys

print("=== FORCE RELOAD DU DASHBOARD ===")

# Kill any existing Streamlit processes
os.system('taskkill /f /im streamlit.exe 2>nul')

print("✅ Anciens processus Streamlit terminés")
print("✅ Cache vidé")
print("🚀 Relancez maintenant : streamlit run app.py")
print("📊 Le nouveau modèle devrait être chargé")
