#!/usr/bin/env python
"""Test SMTP Configuration"""
from flask import Flask
from flask_mail import Mail, Message
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

print('=' * 60)
print('📧 VÉRIFICATION DE LA CONFIGURATION SMTP')
print('=' * 60)
print(f'Serveur: {app.config["MAIL_SERVER"]}')
print(f'Port: {app.config["MAIL_PORT"]}')
print(f'TLS: {app.config["MAIL_USE_TLS"]}')
print(f'Email: {app.config["MAIL_USERNAME"]}')
print(f'Sender: {app.config["MAIL_DEFAULT_SENDER"]}')
print('=' * 60)

try:
    with app.app_context():
        msg = Message(
            subject='Test Configuration SMTP',
            recipients=['abrouguiazer1920@gmail.com'],
            body='Ceci est un email de test pour vérifier la configuration SMTP.'
        )
        mail.send(msg)
        print('✅ EMAIL ENVOYÉ AVEC SUCCÈS!')
        print('Vérifiez votre boîte de réception.')
except Exception as e:
    print(f'❌ ERREUR: {str(e)}')
    print(f'Type: {type(e).__name__}')
