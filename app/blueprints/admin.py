"""
Admin blueprint - user management and system administration
Includes MS-4 API endpoints and admin web interface
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User, UserRole
from app.security import admin_required
from datetime import datetime

admin_bp = Blueprint('admin', __name__)


# ============================================================================
# MS-4 API ENDPOINTS
# ============================================================================

@admin_bp.route('/users', methods=['GET'])
@admin_required
def api_users_list():
    """
    MS-4 API: GET /admin/users
    List all users (system_admin only)
    Returns JSON list of users
    """
    users = User.query.all()
    return jsonify({
        'status': 'success',
        'data': [
            {
                'id': u.id,
                'username': u.username,
                'role': u.role,
                'is_active': u.is_active,
                'created_at': u.created_at.isoformat(),
            }
            for u in users
        ]
    })


@admin_bp.route('/users', methods=['POST'])
@admin_required
def api_users_create():
    """
    MS-4 API: POST /admin/users
    Create new user (system_admin only)
    Expects JSON: {username, password, role}
    """
    try:
        data = request.get_json()
        
        # Validation
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', '')
        
        if not username or not email or not password or not role:
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        if not UserRole.is_valid(role):
            return jsonify({
                'status': 'error',
                'message': f'Invalid role. Must be one of: {", ".join(UserRole.ALL_ROLES)}'
            }), 400
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            return jsonify({'status': 'error', 'message': 'User already exists'}), 409
            
        if User.query.filter_by(email=email).first():
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 409
        
        # Create user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'User {username} created successfully',
            'data': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@admin_bp.route('/health', methods=['GET'])
def health():
    """
    MS-4 API: GET /admin/health
    System health check endpoint
    Returns system status
    """
    try:
        # Test database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception:
        db_status = 'unhealthy'
    
    return jsonify({
        'status': 'success',
        'data': {
            'service': 'Network Slicing Dashboard',
            'version': '1.0.0',
            'database': db_status,
            'timestamp': datetime.utcnow().isoformat(),
        }
    })


@admin_bp.route('/logs', methods=['GET'])
@admin_required
def api_logs():
    """
    MS-4 API: GET /admin/logs
    Get system integration logs
    Returns recent logs
    """
    from app.models.logs import IntegrationLog
    
    limit = request.args.get('limit', 50, type=int)
    logs = IntegrationLog.query.order_by(IntegrationLog.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'status': 'success',
        'data': [
            {
                'id': log.id,
                'service': log.service,
                'endpoint': log.endpoint,
                'status_code': log.status_code,
                'latency_ms': log.latency_ms,
                'created_at': log.created_at.isoformat(),
            }
            for log in logs
        ]
    })


# ============================================================================
# WEB INTERFACE ROUTES
# ============================================================================

@admin_bp.route('/users/web', methods=['GET'])
@admin_required
def users_list():
    """
    Web interface: List users with pagination
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    pagination = User.query.paginate(page=page, per_page=per_page)
    users = pagination.items
    
    return render_template(
        'admin/users.html',
        users=users,
        pagination=pagination,
        title='Gestion des Utilisateurs'
    )


@admin_bp.route('/users/web/create', methods=['GET', 'POST'])
@admin_required
def users_create():
    """
    Web interface: Create new user
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '')
        
        # Validation
        if not username or not email or not password or not role:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('admin.users_create'))
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('admin.users_create'))
        
        if len(password) < 12:
            flash('Le mot de passe doit contenir au moins 12 caractères.', 'danger')
            return redirect(url_for('admin.users_create'))
        
        if not UserRole.is_valid(role):
            flash('Rôle invalide.', 'danger')
            return redirect(url_for('admin.users_create'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Cet utilisateur existe déjà.', 'danger')
            return redirect(url_for('admin.users_create'))
            
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('admin.users_create'))
        
        # Create user
        try:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash(f'Utilisateur {username} créé avec succès.', 'success')
            return redirect(url_for('admin.users_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
            return redirect(url_for('admin.users_create'))
    
    return render_template('admin/create_user.html', roles=UserRole.ALL_ROLES)


@admin_bp.route('/users/web/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def users_edit(user_id):
    """
    Web interface: Edit user (role, status)
    """
    user = User.query.get_or_404(user_id)
    
    # Prevent editing oneself
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre compte.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', '')
        is_active = request.form.get('is_active') == 'on'
        
        if not email:
            flash('L\'email est requis.', 'danger')
            return redirect(url_for('admin.users_edit', user_id=user_id))
            
        if email != user.email and User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('admin.users_edit', user_id=user_id))
        
        if not UserRole.is_valid(role):
            flash('Rôle invalide.', 'danger')
            return redirect(url_for('admin.users_edit', user_id=user_id))
        
        try:
            user.email = email
            user.role = role
            user.is_active = is_active
            db.session.commit()
            
            flash(f'Utilisateur {user.username} mis à jour.', 'success')
            return redirect(url_for('admin.users_list'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
    
    return render_template(
        'admin/edit_user.html',
        user=user,
        roles=UserRole.ALL_ROLES,
        role_labels=UserRole.ROLE_LABELS
    )


@admin_bp.route('/users/web/<int:user_id>/deactivate', methods=['POST'])
@admin_required
def users_deactivate(user_id):
    """
    Web interface: Deactivate user (logical deletion)
    """
    user = User.query.get_or_404(user_id)
    
    # Prevent deactivating oneself
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'danger')
        return redirect(url_for('admin.users_list'))
    
    try:
        user.is_active = False
        db.session.commit()
        
        flash(f'Utilisateur {user.username} désactivé.', 'success')
        return redirect(url_for('admin.users_list'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('admin.users_list'))
