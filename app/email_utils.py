"""
Email utilities - Send verification OTP and password reset tokens
"""
from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, otp_code):
    """
    Send OTP verification email to user
    OTP is already generated and saved to database
    Returns True if sent successfully
    """
    try:
        msg = Message(
            subject='Network Slicing Dashboard - Vérification Email',
            recipients=[user.email],
            html=render_template(
                'emails/verify_email.html',
                username=user.username,
                otp=otp_code
            )
        )
        
        mail.send(msg)
        logger.info(f"✓ Verification email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"✗ Error sending verification email to {user.email}: {str(e)}")
        logger.error(f"  Mail Server: {current_app.config.get('MAIL_SERVER')}")
        logger.error(f"  Mail Port: {current_app.config.get('MAIL_PORT')}")
        logger.error(f"  Mail Use TLS: {current_app.config.get('MAIL_USE_TLS')}")
        
        # Email failed but OTP is already in database
        print(f"\n⚠️ EMAIL FAILED - OTP ALREADY SAVED IN DATABASE")
        print(f"User can now verify with OTP: {otp_code}\n")
        
        return False


def send_password_reset_email(user, reset_url):
    """
    Send password reset link via email
    Reset token is already generated and saved to database
    Returns True if sent successfully
    """
    try:
        msg = Message(
            subject='Network Slicing Dashboard - Réinitialisation Mot de Passe',
            recipients=[user.email],
            html=render_template(
                'emails/reset_password.html',
                username=user.username,
                reset_url=reset_url,
                token=user.reset_token
            )
        )
        
        mail.send(msg)
        logger.info(f"✓ Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"✗ Error sending password reset email to {user.email}: {str(e)}")
        
        # Email failed but token is already in database
        print(f"\n⚠️ EMAIL FAILED - RESET TOKEN ALREADY SAVED IN DATABASE")
        print(f"User can reset password via: {reset_url}\n")
        
        return False
