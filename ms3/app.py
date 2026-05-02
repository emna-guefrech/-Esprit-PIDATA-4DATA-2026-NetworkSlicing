from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import json
import os
from models import db, Alert, Threshold, SliceState

app = Flask(__name__, template_folder='templates')
app.secret_key = 'network_slicing_secret_key_2024'

# Storage for demo users (in production, use database)
demo_users = {
    'admin': {
        'username': 'admin',
        'email': 'admin@networkslicing.com',
        'password': 'admin'
    }
}

# Database configuration (même que MS-1)
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")  # Mot de passe vide comme MS-1
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_NAME = os.environ.get("DB_NAME", "network_slicing_")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# MS-1 Configuration
MS1_URL = os.environ.get("MS1_URL", "http://localhost:5001")

# MS-5 Configuration
MS5_URL = os.environ.get("MS5_URL", "http://localhost:5005")

db.init_app(app)

# Authentication middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/login')
def login():
    """Login page"""
    return render_template('login.html')

@app.route('/auth/login', methods=['POST'])
def auth_login():
    """Handle login authentication"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Check default credentials first
        default_credentials = [
            {'username': 'admin', 'password': 'admin'},
            {'username': 'user', 'password': 'password'},
            {'username': 'network', 'password': 'slicing'}
        ]
        
        is_valid = any(cred['username'] == username and cred['password'] == password 
                      for cred in default_credentials)
        
        # If not in default, check demo users from signup
        if not is_valid and username in demo_users:
            user_data = demo_users[username]
            if isinstance(user_data, dict):
                is_valid = user_data.get('password') == password
            else:
                is_valid = user_data == password
        
        if is_valid:
            session['logged_in'] = True
            session['username'] = username
            return jsonify({'status': 'success', 'redirect': '/'})
        else:
            return jsonify({'status': 'error', 'message': 'Nom d utilisateur ou mot de passe incorrect'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect('/login')

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    username = session.get('username', 'Unknown')
    return render_template('profile.html', username=username)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard page"""
    username = session.get('username', 'Unknown')
    return render_template('admin_dashboard.html', username=username)


@app.route('/api/user-info')
@login_required
def get_user_info():
    """Get current user information"""
    try:
        username = session.get('username', 'Unknown')
        
        print(f"🔍 Looking for user: {username}")
        print(f"📊 demo_users: {demo_users}")
        
        # Get user data from demo_users (stored during signup)
        user_data = demo_users.get(username, {
            'username': username,
            'email': f'{username.lower()}@networkslicing.com',
            'role': 'Network Engineer',
            'department': 'Operations'
        })
        
        print(f"👤 User data found: {user_data}")
        
        # Add statistics
        user_data.update({
            'login_count': 247,
            'slices_created': 89,
            'alerts_managed': 156
        })
        
        return jsonify({'status': 'success', 'data': user_data})
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/signup')
def signup():
    """Signup page"""
    return render_template('signup.html')

@app.route('/auth/signup', methods=['POST'])
def auth_signup():
    """Handle user signup"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password or not confirm_password or not role:
            return jsonify({'status': 'error', 'message': 'Veuillez remplir tous les champs.'})
        
        # Validate role
        valid_roles = ['system_admin', 'network_engineer', 'data_scientist', 'noc_operator']
        if role not in valid_roles:
            return jsonify({'status': 'error', 'message': 'Rôle sélectionné invalide.'})
        
        # Check passwords match
        if password != confirm_password:
            return jsonify({'status': 'error', 'message': 'Les mots de passe ne correspondent pas.'})
        
        # Password requirements
        if len(password) < 12:
            return jsonify({'status': 'error', 'message': 'Le mot de passe doit contenir au moins 12 caractères.'})
        
        # For demo purposes, we'll just simulate user creation
        # In a real application, you would save to database
        
        # Check if username already exists in demo users
        if username in demo_users:
            return jsonify({'status': 'error', 'message': 'Ce nom d utilisateur existe déjà.'})
        
        # Check if username exists in default credentials
        default_usernames = ['admin', 'user', 'network']
        if username in default_usernames:
            return jsonify({'status': 'error', 'message': 'Ce nom d utilisateur existe déjà.'})
        
        # Save user to demo storage
        demo_users[username] = {
            'username': username,
            'email': email,
            'password': password,
            'role': role
        }
        print(f"✅ New user created: {username} ({email}) - Role: {role}")
        print(f"📝 Current demo users: {list(demo_users.keys())}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Compte créé avec succès! Vous pouvez maintenant vous connecter.'
        })
        
    except Exception as e:
        print(f"Error during signup: {e}")
        return jsonify({'status': 'error', 'message': 'Erreur lors de la création du compte.'}), 500

# API Routes
@app.route('/dashboard/slices', methods=['GET'])
def get_dashboard_slices():
    """Get status of all active slices from database"""
    try:
        slices = SliceState.query.order_by(SliceState.last_updated.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [slice.to_dict() for slice in slices],
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alerts', methods=['GET'])
def get_dashboard_alerts():
    """Get active alerts (WARN/CRITICAL)"""
    try:
        alerts = Alert.query.filter_by(acknowledged=False).order_by(Alert.created_at.desc()).all()
        return jsonify({
            'status': 'success',
            'data': [alert.to_dict() for alert in alerts],
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/threshold', methods=['POST'])
def configure_threshold():
    """Configure monitoring thresholds"""
    try:
        data = request.get_json()
        
        if not data or 'metric' not in data:
            return jsonify({'status': 'error', 'message': 'Missing metric field'}), 400
        
        # Check if threshold already exists
        existing = Threshold.query.filter_by(metric=data['metric']).first()
        if existing:
            existing.warn_value = data.get('warn_value')
            existing.critical_value = data.get('critical_value')
        else:
            new_threshold = Threshold(
                metric=data['metric'],
                warn_value=data.get('warn_value'),
                critical_value=data.get('critical_value')
            )
            db.session.add(new_threshold)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Threshold configured successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/ack', methods=['POST'])
def acknowledge_alert():
    """Acknowledge an alert"""
    try:
        data = request.get_json()
        
        if not data or 'alert_id' not in data:
            return jsonify({'status': 'error', 'message': 'Missing alert_id field'}), 400
        
        alert = Alert.query.get(data['alert_id'])
        if not alert:
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
        
        alert.acknowledged = True
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert acknowledged successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert', methods=['POST'])
def create_alert():
    """Create a new alert"""
    try:
        data = request.get_json()
        
        if not data or 'slice_id' not in data or 'level' not in data:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        alert = Alert(
            slice_id=data['slice_id'],
            level=data['level'],
            message=data.get('message', f'{data["level"]} alert for {data["slice_id"]}')
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert created successfully',
            'alert': alert.to_dict()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Alert deleted successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/test/critical', methods=['POST'])
def create_critical_test():
    """Créer une alerte CRITICAL de test"""
    try:
        # Simuler une slice critique
        test_data = {
            "slice_id": "test_critical_001",
            "pipeline": "6G",
            "qos_score": 0.15,  # Très bas
            "congestion_level": "Critical",
            "latency_budget": 200,
            "slice_latency": 500,  # 2.5x le budget
            "packet_loss_budget": 0.01,
            "slice_packet_loss": 0.03,  # 3x le budget
            "jitter_budget": 50,
            "slice_jitter": 120,
            "data_rate_budget": 5,
            "slice_transfer_rate": 2
        }
        
        # Utiliser la fonction de sync existante
        result = sync_prediction_from_ms1()
        return jsonify({
            'status': 'success',
            'message': 'Critical test alert created successfully',
            'test_data': test_data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/test/medium', methods=['POST'])
def create_medium_test():
    """Créer une alerte MEDIUM de test"""
    try:
        # Simuler une slice medium
        test_data = {
            "slice_id": "test_medium_001",
            "pipeline": "5G",
            "qos_score": 0.45,  # Moyen
            "congestion_level": "Light",
            "latency_budget": 200,
            "slice_latency": 280,  # 1.4x le budget
            "packet_loss_budget": 0.01,
            "slice_packet_loss": 0.015,  # 1.5x le budget
            "jitter_budget": 50,
            "slice_jitter": 70,
            "data_rate_budget": 5,
            "slice_transfer_rate": 4
        }
        
        # Créer la slice et l'alerte
        existing_slice = SliceState.query.filter_by(slice_id=test_data["slice_id"]).first()
        if not existing_slice:
            new_slice = SliceState(**test_data)
            db.session.add(new_slice)
        else:
            # Mettre à jour
            for key, value in test_data.items():
                if hasattr(existing_slice, key):
                    setattr(existing_slice, key, value)
        
        # Créer l'alerte medium
        alert = Alert(
            slice_id=test_data["slice_id"],
            level='WARN',
            message=f'⚠️ MEDIUM TEST ALERT - Slice {test_data["slice_id"]}: Light congestion, QoS: {test_data["qos_score"]:.3f}'
        )
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Medium test alert created successfully',
            'test_data': test_data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/populate/critical', methods=['POST'])
def populate_critical_slices():
    """Populate database with critical slices automatically"""
    try:
        critical_slices_data = [
            {
                "slice_id": "critical_slice_001",
                "pipeline": "6G",
                "qos_score": 0.12,  # Very low
                "congestion_level": "Critical",
                "latency_budget": 150,
                "slice_latency": 450,  # 3x budget
                "packet_loss_budget": 0.008,
                "slice_packet_loss": 0.025,  # 3x budget
                "jitter_budget": 40,
                "slice_jitter": 130,  # 3x budget
                "data_rate_budget": 8,
                "slice_transfer_rate": 2
            },
            {
                "slice_id": "critical_slice_002", 
                "pipeline": "5G",
                "qos_score": 0.08,  # Extremely low
                "congestion_level": "Critical",
                "latency_budget": 200,
                "slice_latency": 600,  # 3x budget
                "packet_loss_budget": 0.01,
                "slice_packet_loss": 0.035,  # 3.5x budget
                "jitter_budget": 50,
                "slice_jitter": 160,  # 3x budget
                "data_rate_budget": 10,
                "slice_transfer_rate": 1.5
            },
            {
                "slice_id": "critical_slice_003",
                "pipeline": "6G", 
                "qos_score": 0.15,  # Very low
                "congestion_level": "Critical",
                "latency_budget": 100,
                "slice_latency": 350,  # 3.5x budget
                "packet_loss_budget": 0.005,
                "slice_packet_loss": 0.020,  # 4x budget
                "jitter_budget": 30,
                "slice_jitter": 110,  # 3.5x budget
                "data_rate_budget": 12,
                "slice_transfer_rate": 3
            },
            {
                "slice_id": "critical_slice_004",
                "pipeline": "5G",
                "qos_score": 0.05,  # Extremely low
                "congestion_level": "Critical", 
                "latency_budget": 180,
                "slice_latency": 540,  # 3x budget
                "packet_loss_budget": 0.012,
                "slice_packet_loss": 0.048,  # 4x budget
                "jitter_budget": 45,
                "slice_jitter": 150,  # 3x budget
                "data_rate_budget": 6,
                "slice_transfer_rate": 1
            },
            {
                "slice_id": "critical_slice_005",
                "pipeline": "6G",
                "qos_score": 0.18,  # Very low
                "congestion_level": "Critical",
                "latency_budget": 120,
                "slice_latency": 380,  # 3x budget
                "packet_loss_budget": 0.006,
                "slice_packet_loss": 0.022,  # 3.5x budget
                "jitter_budget": 35,
                "slice_jitter": 125,  # 3.5x budget
                "data_rate_budget": 9,
                "slice_transfer_rate": 2.5
            }
        ]
        
        created_slices = []
        created_alerts = []
        
        for slice_data in critical_slices_data:
            # Check if slice already exists
            existing_slice = SliceState.query.filter_by(slice_id=slice_data["slice_id"]).first()
            
            if not existing_slice:
                # Create new critical slice
                new_slice = SliceState(**slice_data)
                db.session.add(new_slice)
                created_slices.append(slice_data["slice_id"])
            else:
                # Update existing slice
                for key, value in slice_data.items():
                    if hasattr(existing_slice, key):
                        setattr(existing_slice, key, value)
            
            # Create CRITICAL alert for each slice
            existing_alert = Alert.query.filter_by(slice_id=slice_data["slice_id"], level='CRITICAL').first()
            if not existing_alert:
                alert = Alert(
                    slice_id=slice_data["slice_id"],
                    level='CRITICAL',
                    message=f'🚨 CRITICAL - Slice {slice_data["slice_id"]}: {slice_data["congestion_level"]} congestion, QoS: {slice_data["qos_score"]:.3f}'
                )
                db.session.add(alert)
                created_alerts.append(slice_data["slice_id"])
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Database populated with {len(critical_slices_data)} critical slices',
            'created_slices': len(created_slices),
            'created_alerts': len(created_alerts),
            'total_critical_slices': len(critical_slices_data)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/slice', methods=['POST'])
def create_slice():
    """Create a new slice (mock implementation)"""
    try:
        data = request.get_json()
        
        if not data or 'slice_id' not in data:
            return jsonify({'status': 'error', 'message': 'Missing slice_id'}), 400
        
        # Mock implementation - in real case, would call MS-1 and MS-2
        return jsonify({
            'status': 'success',
            'message': f'Slice {data["slice_id"]} created successfully',
            'slice_id': data['slice_id']
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/slice/<string:slice_id>', methods=['DELETE'])
def delete_slice(slice_id):
    """Delete a slice (mock implementation)"""
    try:
        # Delete from database
        slice_state = SliceState.query.filter_by(slice_id=slice_id).first()
        if slice_state:
            db.session.delete(slice_state)
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Slice {slice_id} deleted successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/sync/prediction', methods=['POST'])
def sync_prediction_from_ms1():
    """Recevoir les prédictions de MS-1 et créer/mettre à jour un slice"""
    try:
        data = request.get_json()
        
        if not data or 'slice_id' not in data:
            return jsonify({'status': 'error', 'message': 'Missing slice_id'}), 400
        
        slice_id = data['slice_id']
        pipeline = data.get('pipeline', '6G')
        qos_score = data.get('qos_score')
        congestion_level = data.get('congestion_level', 'Normal')
        
        # Check if slice already exists
        existing_slice = SliceState.query.filter_by(slice_id=slice_id).first()
        
        if existing_slice:
            # Update existing slice
            existing_slice.qos_score = qos_score
            existing_slice.congestion_level = congestion_level
            existing_slice.pipeline = pipeline.upper()
            existing_slice.last_updated = datetime.utcnow()
            
            # Update metrics if provided
            if 'latency_budget' in data:
                existing_slice.latency_budget = data['latency_budget']
                existing_slice.slice_latency = data['slice_latency']
                existing_slice.packet_loss_budget = data['packet_loss_budget']
                existing_slice.slice_packet_loss = data['slice_packet_loss']
                existing_slice.jitter_budget = data['jitter_budget']
                existing_slice.slice_jitter = data['slice_jitter']
                existing_slice.data_rate_budget = data['data_rate_budget']
                existing_slice.slice_transfer_rate = data['slice_transfer_rate']
        else:
            # Create new slice
            new_slice = SliceState(
                slice_id=slice_id,
                pipeline=pipeline.upper(),
                qos_score=qos_score,
                congestion_level=congestion_level,
                latency_budget=data.get('latency_budget'),
                slice_latency=data.get('slice_latency'),
                packet_loss_budget=data.get('packet_loss_budget'),
                slice_packet_loss=data.get('slice_packet_loss'),
                jitter_budget=data.get('jitter_budget'),
                slice_jitter=data.get('slice_jitter'),
                data_rate_budget=data.get('data_rate_budget'),
                slice_transfer_rate=data.get('slice_transfer_rate')
            )
            db.session.add(new_slice)
        
        db.session.commit()
        
        # Check if alert needed based on congestion level and QoS score
        alerts_created = []
        
        # ALERTES CRITICAL À CHAQUE PRÉDICTION (plus de déduplication)
        # Critical alerts (rouge) - SEULEMENT si congestion_level == 'Critical'
        print(f"🔍 DEBUG MS-3 - congestion_level: {congestion_level}, qos_score: {qos_score}")
        
        if congestion_level == 'Critical':
            print(f"🔍 DEBUG MS-3 - Congestion CRITICAL détectée pour slice: {slice_id}")
            
            # CRÉER UNE ALERTE CRITICAL À CHAQUE FOIS (pas de vérification de doublons)
            print(f"🔍 DEBUG MS-3 - Création d'une NOUVELLE alerte CRITICAL pour slice: {slice_id}")
            alert = Alert(
                slice_id=slice_id,
                level='CRITICAL',
                message=f'🚨 CRITICAL ALERT - Slice {slice_id}: {congestion_level} congestion, QoS: {qos_score:.3f}'
            )
            db.session.add(alert)
            alerts_created.append('CRITICAL')
            print(f"🔍 DEBUG MS-3 - NOUVELLE Alert CRITICAL créée avec succès")
        else:
            print(f"🔍 DEBUG MS-3 - Pas d'alerte (congestion: {congestion_level})")
        
        # PAS D'ALERTES du tout pour Normal ou Light
        # PAS D'ALERTES de métriques supplémentaires
        
        if alerts_created:
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Slice {slice_id} synchronized successfully',
            'alerts_created': len(alerts_created),
            'slice_data': existing_slice.to_dict() if existing_slice else new_slice.to_dict()
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts (toutes les alertes, pas de nettoyage)"""
    try:
        # Récupérer TOUTES les alertes sans nettoyage
        alerts = Alert.query.order_by(Alert.created_at.desc()).all()
        print(f"🔍 DEBUG GET_ALERTS - Nombre total d'alertes: {len(alerts)}")
        
        # Afficher les alertes pour debug
        for alert in alerts:
            print(f"🔍 DEBUG GET_ALERTS - Alerte: {alert.slice_id} - {alert.level} - {alert.message}")
        
        return jsonify({
            'status': 'success',
            'data': [alert.to_dict() for alert in alerts]
        })
    except Exception as e:
        print(f"🔍 DEBUG GET_ALERTS - ERREUR: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/thresholds', methods=['GET'])
def get_thresholds():
    """Get all configured thresholds"""
    try:
        thresholds = Threshold.query.all()
        return jsonify({
            'status': 'success',
            'data': [threshold.to_dict() for threshold in thresholds]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Dashboard UI Routes
@app.route('/')
@login_required
def dashboard_main():
    """Main dashboard with single page application"""
    username = session.get('username', 'Unknown')
    user_data = demo_users.get(username, {})
    
    print(f"🔍 DEBUG - Username: {username}")
    print(f"🔍 DEBUG - demo_users keys: {list(demo_users.keys())}")
    print(f"🔍 DEBUG - user_data: {user_data}")
    print(f"🔍 DEBUG - email: {user_data.get('email', f'{username.lower()}@networkslicing.com')}")
    
    return render_template('spa.html', 
                         username=username,
                         user_email=user_data.get('email', f'{username.lower()}@networkslicing.com'),
                         user_role=user_data.get('role', 'Network Engineer'),
                         user_department=user_data.get('department', 'Operations'))

@app.route('/test')
def test_simple():
    """Simple test page"""
    return render_template('test_nav.html')

@app.route('/fixed')
def dashboard_fixed():
    """Fixed dashboard page"""
    return render_template('dashboard_with_nav.html')

def save_prediction_to_db(input_data, result_data):
    """Save prediction result to database - ALWAYS ADD/UPDATE SLICE"""
    try:
        slice_id = result_data.get('slice_id', input_data.get('slice_id'))
        
        # Check if slice already exists
        existing_slice = SliceState.query.filter_by(slice_id=slice_id).first()
        
        if existing_slice:
            # Update existing slice with prediction results
            existing_slice.pipeline = result_data.get('pipeline', input_data.get('pipeline'))
            existing_slice.qos_score = result_data.get('qos_score')
            existing_slice.congestion_level = result_data.get('congestion_level')
            existing_slice.latency_budget = input_data.get('latency_budget')
            existing_slice.slice_latency = input_data.get('slice_latency') or input_data.get('cong_latency')
            existing_slice.packet_loss_budget = input_data.get('packet_loss_budget')
            existing_slice.slice_packet_loss = input_data.get('slice_packet_loss') or input_data.get('cong_packet_loss')
            existing_slice.jitter_budget = input_data.get('jitter_budget')
            existing_slice.slice_jitter = input_data.get('slice_jitter') or input_data.get('cong_jitter')
            existing_slice.data_rate_budget = input_data.get('data_rate_budget')
            existing_slice.slice_transfer_rate = input_data.get('slice_transfer_rate')
            existing_slice.last_updated = datetime.utcnow()
            print(f"Updated existing slice: {slice_id}")
        else:
            # Create new slice from prediction
            new_slice = SliceState(
                slice_id=slice_id,
                pipeline=result_data.get('pipeline', input_data.get('pipeline')),
                qos_score=result_data.get('qos_score'),
                congestion_level=result_data.get('congestion_level'),
                latency_budget=input_data.get('latency_budget'),
                slice_latency=input_data.get('slice_latency') or input_data.get('cong_latency'),
                packet_loss_budget=input_data.get('packet_loss_budget'),
                slice_packet_loss=input_data.get('slice_packet_loss') or input_data.get('cong_packet_loss'),
                jitter_budget=input_data.get('jitter_budget'),
                slice_jitter=input_data.get('slice_jitter') or input_data.get('cong_jitter'),
                data_rate_budget=input_data.get('data_rate_budget'),
                slice_transfer_rate=input_data.get('slice_transfer_rate'),
                status='active'
            )
            db.session.add(new_slice)
            print(f"Created new slice from prediction: {slice_id}")
        
        db.session.commit()
        print(f"✅ Prediction saved and slice added/updated: {slice_id}")
        
        # Create alert if congestion is critical
        if result_data.get('congestion_level') == 'Critical':
            create_critical_alert(slice_id, result_data)
        
    except Exception as e:
        print(f"❌ Error saving prediction to database: {e}")
        db.session.rollback()

def create_critical_alert(slice_id, prediction_data):
    """Create a critical alert for prediction"""
    try:
        alert = Alert(
            slice_id=slice_id,
            level='CRITICAL',
            message=f"Critical congestion detected for slice {slice_id}. QoS Score: {prediction_data.get('qos_score', 0):.3f}",
            acknowledged=False
        )
        db.session.add(alert)
        db.session.commit()
        print(f"Critical alert created for slice {slice_id}")
    except Exception as e:
        print(f"Error creating alert: {e}")
        db.session.rollback()

@app.route('/predict/qos', methods=['POST'])
def proxy_predict_qos():
    """Proxy pour MS-1 QoS prediction"""
    try:
        data = request.get_json()
        response = requests.post(f"{MS1_URL}/predict/qos", json=data, timeout=10)
        result = response.json()
        
        # Save prediction to database
        save_prediction_to_db(data, result)
        
        return result, response.status_code
    except Exception as e:
        # Return demo data if MS-1 is not available
        import random
        demo_result = {
            'qos_score': round(random.uniform(0.3, 0.9), 3),
            'congestion_level': random.choice(['Normal', 'Light', 'Critical']),
            'pipeline': data.get('pipeline', '6G'),
            'slice_id': data.get('slice_id', 'demo_slice'),
            'bandwidth': data.get('bandwidth', 100),
            'latency': data.get('slice_latency', 50),
            'packet_loss': data.get('slice_packet_loss', 0.01),
            'jitter': data.get('slice_jitter', 2.0),
            'data_rate': data.get('slice_transfer_rate', 5.0)
        }
        
        # Save demo prediction to database
        save_prediction_to_db(data, demo_result)
        
        return jsonify(demo_result), 200

@app.route('/predict/congestion', methods=['POST'])
def proxy_predict_congestion():
    """Proxy pour MS-1 congestion prediction"""
    try:
        data = request.get_json()
        response = requests.post(f"{MS1_URL}/predict/congestion", json=data, timeout=10)
        result = response.json()
        
        # Save prediction to database
        save_prediction_to_db(data, result)
        
        return result, response.status_code
    except Exception as e:
        # Return demo data if MS-1 is not available
        import random
        demo_result = {
            'qos_score': round(random.uniform(0.3, 0.9), 3),
            'congestion_level': random.choice(['Normal', 'Light', 'Critical']),
            'pipeline': data.get('pipeline', '6G'),
            'slice_id': data.get('slice_id', 'demo_slice'),
            'bandwidth': data.get('bandwidth', 100),
            'traffic_load': data.get('traffic_load', 50),
            'packet_loss': data.get('cong_packet_loss', 0.01),
            'latency': data.get('cong_latency', 50),
            'jitter': data.get('cong_jitter', 2.0),
            'queue_length': data.get('queue_length', 10)
        }
        
        # Save demo prediction to database
        save_prediction_to_db(data, demo_result)
        
        return jsonify(demo_result), 200

@app.route('/api/ms1/stats', methods=['GET'])
def proxy_ms1_stats():
    """Proxy pour MS-1 stats API"""
    try:
        response = requests.get(f"{MS1_URL}/stats", timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        # Return demo data if MS-1 is not available
        import random
        demo_stats = {
            'total': random.randint(10, 60),
            'normal': random.randint(5, 35),
            'critical': random.randint(1, 6)
        }
        return jsonify(demo_stats), 200

@app.route('/api/predictions', methods=['GET'])
def proxy_get_predictions():
    """Get predictions from local database"""
    try:
        # Try to get from MS-1 first
        response = requests.get(f"{MS1_URL}/api/predictions", timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        # Get from local database if MS-1 is not available
        try:
            slices = SliceState.query.order_by(SliceState.last_updated.desc()).limit(10).all()
            
            predictions = []
            for slice in slices:
                predictions.append({
                    'id': slice.id,
                    'slice_id': slice.slice_id,
                    'pipeline': slice.pipeline,
                    'qos_score': slice.qos_score,
                    'congestion_level': slice.congestion_level,
                    'created_at': slice.last_updated.isoformat() if slice.last_updated else datetime.utcnow().isoformat()
                })
            
            return jsonify(predictions), 200
            
        except Exception as db_error:
            print(f"Database error: {db_error}")
            # Return empty array if database also fails
            return jsonify([]), 200

@app.route('/api/prediction/<int:prediction_id>', methods=['DELETE'])
def proxy_delete_prediction(prediction_id):
    """Proxy pour MS-1 delete prediction"""
    try:
        response = requests.delete(f"{MS1_URL}/api/prediction/{prediction_id}", timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        return jsonify({'error': f'Proxy error: {str(e)}'}), 500

@app.route('/api/alerts', methods=['GET'])
def get_critical_alerts():
    """Get unacknowledged critical alerts"""
    try:
        alerts = Alert.query.filter_by(level='CRITICAL', acknowledged=False).order_by(Alert.created_at.desc()).limit(10).all()
        
        alert_list = []
        for alert in alerts:
            alert_list.append({
                'id': alert.id,
                'slice_id': alert.slice_id,
                'level': alert.level,
                'message': alert.message,
                'created_at': alert.created_at.isoformat() if alert.created_at else None
            })
        
        return jsonify(alert_list), 200
        
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return jsonify([]), 200

@app.route('/api/alert/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_critical_alert(alert_id):
    """Acknowledge an alert"""
    try:
        alert = Alert.query.get(alert_id)
        if alert:
            alert.acknowledged = True
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Alert acknowledged'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
            
    except Exception as e:
        print(f"Error acknowledging alert: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/slices', methods=['POST'])
def add_slice():
    """Add a new slice to the database"""
    try:
        data = request.get_json()
        
        # Check if slice already exists
        existing_slice = SliceState.query.filter_by(slice_id=data.get('slice_id')).first()
        if existing_slice:
            return jsonify({'error': 'Slice already exists'}), 400
        
        # Create new slice
        new_slice = SliceState(
            slice_id=data.get('slice_id'),
            pipeline=data.get('pipeline', '6G'),
            qos_score=data.get('qos_score'),
            congestion_level=data.get('congestion_level', 'Normal'),
            latency_budget=data.get('latency_budget'),
            slice_latency=data.get('slice_latency'),
            packet_loss_budget=data.get('packet_loss_budget'),
            slice_packet_loss=data.get('slice_packet_loss'),
            jitter_budget=data.get('jitter_budget'),
            slice_jitter=data.get('slice_jitter'),
            data_rate_budget=data.get('data_rate_budget'),
            slice_transfer_rate=data.get('slice_transfer_rate'),
            status='active'
        )
        
        db.session.add(new_slice)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Slice added successfully',
            'slice': new_slice.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Error adding slice: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/slices', methods=['GET'])
def get_slices():
    """Get all slices from database"""
    try:
        slices = SliceState.query.order_by(SliceState.last_updated.desc()).all()
        
        slice_list = []
        for slice in slices:
            slice_list.append(slice.to_dict())
        
        return jsonify(slice_list), 200
        
    except Exception as e:
        print(f"Error fetching slices: {e}")
        return jsonify([]), 200

@app.route('/api/slice/<string:slice_id>', methods=['DELETE'])
def delete_slice_api(slice_id):
    """Delete a slice from database"""
    try:
        slice = SliceState.query.filter_by(slice_id=slice_id).first()
        if slice:
            db.session.delete(slice)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Slice deleted'}), 200
        else:
            return jsonify({'error': 'Slice not found'}), 404
            
    except Exception as e:
        print(f"Error deleting slice: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models/health', methods=['GET'])
def proxy_models_health():
    """Proxy for MS-5 health check"""
    try:
        response = requests.get(f"{MS5_URL}/", timeout=3)
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        # MS-5 service not running - return demo data
        return jsonify({
            'status': 'demo',
            'message': 'MS-5 service unavailable - using demo data'
        }), 200
    except requests.exceptions.Timeout:
        # MS-5 service timeout - return demo data
        return jsonify({
            'status': 'demo',
            'message': 'MS-5 service timeout - using demo data'
        }), 200
    except Exception as e:
        # Any other error - return demo data
        return jsonify({
            'status': 'demo',
            'message': f'MS-5 service error - using demo data: {str(e)}'
        }), 200

@app.route('/api/model/metrics', methods=['GET'])
def proxy_model_metrics():
    """Proxy for MS-5 model metrics"""
    try:
        response = requests.get(f"{MS5_URL}/model/metrics", timeout=3)
        return response.json(), response.status_code
    except requests.exceptions.ConnectionError:
        # MS-5 service not running - return demo data
        return jsonify({
            'total_models': 3,
            'models': [
                {
                    'name': 'XGBoost_QoS_6G',
                    'model_name': 'XGBoost_QoS_6G',
                    'version': '1.2',
                    'accuracy': 0.92,
                    'precision': 0.89,
                    'recall': 0.94,
                    'f1_score': 0.91,
                    'r2_score': 0.9542,
                    'rmse': 0.0234,
                    'status': 'active',
                    'type': 'QoS Prediction',
                    'pipeline': '6G'
                },
                {
                    'name': 'RandomForest_5G',
                    'model_name': 'RandomForest_5G', 
                    'version': '1.1',
                    'accuracy': 0.88,
                    'precision': 0.85,
                    'recall': 0.90,
                    'f1_score': 0.87,
                    'r2_score': 0.9123,
                    'rmse': 0.0345,
                    'status': 'active',
                    'type': 'QoS Prediction',
                    'pipeline': '5G'
                },
                {
                    'name': 'SGD_Congestion_6G',
                    'model_name': 'SGD_Congestion_6G',
                    'version': '1.0',
                    'accuracy': 0.85,
                    'precision': 0.82,
                    'recall': 0.88,
                    'f1_score': 0.85,
                    'r2_score': 0.8765,
                    'rmse': 0.0456,
                    'status': 'active',
                    'type': 'Congestion Detection',
                    'pipeline': '6G'
                }
            ]
        }), 200
    except requests.exceptions.Timeout:
        # MS-5 service timeout - return demo data
        return jsonify({
            'total_models': 1,
            'models': [
                {
                    'name': 'XGBoost_QoS_6G',
                    'model_name': 'XGBoost_QoS_6G',
                    'version': '1.2',
                    'accuracy': 0.92,
                    'precision': 0.89,
                    'recall': 0.94,
                    'f1_score': 0.91,
                    'r2_score': 0.9542,
                    'rmse': 0.0234,
                    'status': 'active',
                    'type': 'QoS Prediction',
                    'pipeline': '6G'
                }
            ]
        }), 200
    except Exception as e:
        # Any other error - return demo data
        return jsonify({
            'total_models': 1,
            'models': [
                {
                    'name': 'XGBoost_QoS_6G',
                    'model_name': 'XGBoost_QoS_6G',
                    'version': '1.0',
                    'accuracy': 0.90,
                    'precision': 0.87,
                    'recall': 0.92,
                    'f1_score': 0.89,
                    'r2_score': 0.8901,
                    'rmse': 0.0321,
                    'status': 'demo',
                    'type': 'QoS Prediction',
                    'pipeline': '6G'
                }
            ]
        }), 200

@app.route('/api/dashboard-data')
@login_required
def get_dashboard_data():
    """Get aggregated dashboard data for anomaly section"""
    try:
        slices = SliceState.query.order_by(SliceState.last_updated.desc()).all()
        alerts = Alert.query.filter_by(acknowledged=False).order_by(Alert.created_at.desc()).all()
        
        critical_count = sum(1 for s in slices if s.congestion_level == 'Critical')
        normal_count = sum(1 for s in slices if s.congestion_level == 'Normal')
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_slices': len(slices),
                'critical_slices': critical_count,
                'normal_slices': normal_count,
                'active_alerts': len(alerts),
                'slices': [s.to_dict() for s in slices],
                'alerts': [a.to_dict() for a in alerts]
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prediction/<int:prediction_id>', methods=['PUT'])
def proxy_update_prediction(prediction_id):
    """Proxy pour MS-1 update prediction"""
    try:
        data = request.get_json()
        response = requests.put(f"{MS1_URL}/api/prediction/{prediction_id}", json=data, timeout=10)
        return response.json(), response.status_code
    except Exception as e:
        return jsonify({'error': f'Proxy error: {str(e)}'}), 500

@app.route('/dashboard/alert/<int:alert_id>', methods=['DELETE'])
def delete_alert_route(alert_id):
    """Delete a specific alert"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Alert {alert_id} deleted successfully'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/alert/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update a specific alert"""
    try:
        alert = Alert.query.get(alert_id)
        if not alert:
            return jsonify({'status': 'error', 'message': 'Alert not found'}), 404
        
        data = request.get_json()
        if 'message' in data:
            alert.message = data['message']
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Alert {alert_id} updated successfully',
            'alert': alert.to_dict()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/dashboard/slice/<string:slice_id>', methods=['PUT'])
def update_slice(slice_id):
    """Update a specific slice"""
    try:
        slice_state = SliceState.query.filter_by(slice_id=slice_id).first()
        if not slice_state:
            return jsonify({'status': 'error', 'message': 'Slice not found'}), 404
        
        data = request.get_json()
        
        # Update slice metrics
        if 'latency_budget' in data:
            slice_state.latency_budget = data['latency_budget']
        if 'slice_latency' in data:
            slice_state.slice_latency = data['slice_latency']
        if 'packet_loss_budget' in data:
            slice_state.packet_loss_budget = data['packet_loss_budget']
        if 'slice_packet_loss' in data:
            slice_state.slice_packet_loss = data['slice_packet_loss']
        if 'jitter_budget' in data:
            slice_state.jitter_budget = data['jitter_budget']
        if 'slice_jitter' in data:
            slice_state.slice_jitter = data['slice_jitter']
        if 'data_rate_budget' in data:
            slice_state.data_rate_budget = data['data_rate_budget']
        if 'slice_transfer_rate' in data:
            slice_state.slice_transfer_rate = data['slice_transfer_rate']
        
        slice_state.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Slice {slice_id} updated successfully',
            'slice': slice_state.to_dict()
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health():
    """Health monitor page"""
    return render_template('health.html')

# ... (existing code)
@app.route('/api/qos-history')
def get_qos_history():
    """Get historical QoS data for charts"""
    try:
        # Mock historical data
        # In real implementation, this would aggregate data from MS-2
        history_data = {
            'timestamps': [],
            'bandwidth': [],
            'latency': [],
            'packet_loss': []
        }
        
        # Generate 24 hours of mock data (hourly points)
        base_time = datetime.utcnow() - timedelta(hours=24)
        for i in range(25):
            timestamp = base_time + timedelta(hours=i)
            history_data['timestamps'].append(timestamp.isoformat())
            history_data['bandwidth'].append(75 + (i % 10) * 2)
            history_data['latency'].append(10 + (i % 5) * 2)
            history_data['packet_loss'].append(0.01 + (i % 3) * 0.005)
        
        return jsonify({
            'status': 'success',
            'data': history_data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()
        
        # Initialize default thresholds if none exist
        if Threshold.query.count() == 0:
            default_thresholds = [
                Threshold(metric='bandwidth', warn_value=70.0, critical_value=50.0),
                Threshold(metric='latency', warn_value=20.0, critical_value=50.0),
                Threshold(metric='packet_loss', warn_value=0.02, critical_value=0.05),
                Threshold(metric='jitter', warn_value=3.0, critical_value=5.0)
            ]
            for threshold in default_thresholds:
                db.session.add(threshold)
            db.session.commit()

if __name__ == '__main__':
    create_tables()  # Initialize database
    app.run(host="0.0.0.0", port=5003, debug=True)
