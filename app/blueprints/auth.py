"""
Authentication routes: login, logout, password reset
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


# Note: Email-based password reset is available as a bonus feature
# For V1, password changes are managed through the authenticated profile page


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route
    GET: Display login form
    POST: Process login credentials
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        # Validation
        if not username or not password:
            flash('Veuillez entrer votre nom d\'utilisateur et mot de passe.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user is None or not user.check_password(password):
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user is active
        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez un administrateur.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Login successful
        login_user(user, remember=remember)
        flash(f'Bienvenue {user.username}!', 'success')
        
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))
    
    return render_template('auth/login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User signup/registration route
    GET: Display signup form
    POST: Create new user account
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'network_engineer').strip()
        
        # Validation
        if not username or not email or not password or not confirm_password or not role:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Validate role
        from app.models.user import UserRole
        if not UserRole.is_valid(role):
            flash('Rôle sélectionné invalide.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Check passwords match
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Password requirements
        if len(password) < 12:
            flash('Le mot de passe doit contenir au moins 12 caractères.', 'danger')
            return redirect(url_for('auth.signup'))
        
        # Create new user with selected role
        try:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Generate OTP immediately and save to database
            otp_code = user.generate_otp()
            print(f"\n{'='*60}")
            print(f"📧 OTP CODE GENERATED")
            print(f"{'='*60}")
            print(f"User: {user.username}")
            print(f"Email: {user.email}")
            print(f"OTP Code: {otp_code}")
            print(f"Valid for: 10 minutes")
            print(f"Saved in database: {user.otp_code}")
            print(f"{'='*60}\n")
            
            # Try to send verification email (but OTP is already in database)
            from app.email_utils import send_verification_email
            email_sent = send_verification_email(user, otp_code)
            
            if email_sent:
                flash('✅ Compte créé! Un email de vérification a été envoyé.', 'success')
            else:
                flash('⚠️ Compte créé! Erreur d\'envoi email. Entrez le code OTP de la console.', 'warning')
            
            return redirect(url_for('auth.verify_email', username=username))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during signup: {e}")
            flash('❌ Erreur lors de la création du compte.', 'danger')
            return redirect(url_for('auth.signup'))
    
    return render_template('auth/signup.html')


@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():
    """
    Email verification route using OTP
    GET: Display OTP form
    POST: Verify OTP
    """
    username = request.args.get('username')
    if not username:
        flash('Identifiant manquant.', 'danger')
        return redirect(url_for('auth.signup'))
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash('Utilisateur non trouvé.', 'danger')
        return redirect(url_for('auth.signup'))
    
    if user.email_verified:
        flash('Email déjà vérifié. Vous pouvez vous connecter.', 'info')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp', '').strip()
        
        if not otp_code:
            flash('Veuillez entrer le code OTP.', 'danger')
            return redirect(url_for('auth.verify_email', username=username))
        
        if user.verify_otp(otp_code):
            user.mark_email_verified()
            flash('Email vérifié avec succès! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Code OTP invalide ou expiré.', 'danger')
            return redirect(url_for('auth.verify_email', username=username))
    
    return render_template('auth/verify_email.html', username=username, email=user.email)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    Password reset request route
    GET: Display email form
    POST: Send password reset email
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Veuillez entrer votre email.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token and save to database first
            token = user.generate_reset_token()
            reset_url = f"{request.host_url.rstrip('/')}/auth/reset/{token}"
            
            print(f"\n{'='*60}")
            print(f"🔐 PASSWORD RESET TOKEN GENERATED")
            print(f"{'='*60}")
            print(f"User: {user.username}")
            print(f"Email: {user.email}")
            print(f"Reset URL: {reset_url}")
            print(f"Token: {token}")
            print(f"Valid for: 1 hour")
            print(f"{'='*60}\n")
            
            # Try to send email
            from app.email_utils import send_password_reset_email
            email_sent = send_password_reset_email(user, reset_url)
            
            if not email_sent:
                flash('⚠️ Erreur d\'envoi email. Vérifiez la console pour le lien.', 'warning')
            else:
                flash('✅ Un email de réinitialisation a été envoyé.', 'info')
        else:
            # For security, don't reveal if account exists
            flash('Un email de réinitialisation a été envoyé si le compte existe.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Password reset route via token
    GET: Display password form
    POST: Update password
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Lien de réinitialisation invalide ou expiré.', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not new_password or not confirm_password:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        if len(new_password) < 12:
            flash('Le mot de passe doit contenir au moins 12 caractères.', 'danger')
            return redirect(url_for('auth.reset_password', token=token))
        
        # Update password
        user.set_password(new_password)
        user.clear_reset_token()
        flash('Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)
@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """
    User logout route
    POST: Clear session and redirect to login
    """
    username = current_user.username
    logout_user()
    flash(f'{username}, vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile page - view and edit password
    GET: Display profile form
    POST: Update password
    """
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not old_password or not new_password or not confirm_password:
            flash('Veuillez remplir tous les champs.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check old password
        if not current_user.check_password(old_password):
            flash('Votre mot de passe actuel est incorrect.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Check new passwords match
        if new_password != confirm_password:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Password requirements
        if len(new_password) < 12:
            flash('Le mot de passe doit contenir au moins 12 caractères.', 'danger')
            return redirect(url_for('auth.profile'))
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Votre mot de passe a été changé avec succès.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', user=current_user)
