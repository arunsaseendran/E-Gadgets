"""
OTP Utility Functions for Email Verification
"""
import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache


def generate_otp(length=6):
    """Generate a random 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email, otp):
    """Send OTP to user's email"""
    subject = '🔐 E-Gadgets - Email Verification OTP'
    message = f"""
    Hello!
    
    Your OTP for E-Gadgets registration is: {otp}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this, please ignore this email.
    
    Best regards,
    E-Gadgets Team
    """
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #1e1e1e;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            }}
            .header {{
                background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                color: white;
                font-size: 28px;
            }}
            .content {{
                padding: 40px 30px;
                color: #e0e0e0;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #00d4ff 0%, #0099cc 100%);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp {{
                font-size: 42px;
                font-weight: bold;
                letter-spacing: 8px;
                color: white;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            }}
            .footer {{
                background: #0d0d0d;
                padding: 20px;
                text-align: center;
                color: #888;
                font-size: 14px;
            }}
            .warning {{
                background: rgba(255, 193, 7, 0.1);
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                color: #ffc107;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ E-Gadgets</h1>
            </div>
            <div class="content">
                <h2 style="color: #00d4ff;">Email Verification</h2>
                <p>Hello!</p>
                <p>Thank you for registering with E-Gadgets. Please use the OTP below to verify your email address:</p>
                
                <div class="otp-box">
                    <div class="otp">{otp}</div>
                </div>
                
                <p style="text-align: center; color: #888;">This OTP is valid for <strong style="color: #00d4ff;">10 minutes</strong></p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong><br>
                    If you didn't request this verification, please ignore this email. Never share your OTP with anyone.
                </div>
            </div>
            <div class="footer">
                <p>© 2025 E-Gadgets. All rights reserved.</p>
                <p>Your one-stop destination for cutting-edge electronics.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def store_otp(email, otp):
    """Store OTP in cache with 10-minute expiry"""
    cache_key = f'otp_{email}'
    cache.set(cache_key, otp, timeout=600)  # 10 minutes


def verify_otp(email, otp):
    """Verify if the provided OTP matches the stored one"""
    cache_key = f'otp_{email}'
    stored_otp = cache.get(cache_key)
    
    if stored_otp and stored_otp == otp:
        cache.delete(cache_key)  # Delete OTP after successful verification
        return True
    return False


def store_registration_data(email, data):
    """Store registration data temporarily"""
    cache_key = f'reg_data_{email}'
    cache.set(cache_key, data, timeout=600)  # 10 minutes


def get_registration_data(email):
    """Retrieve stored registration data"""
    cache_key = f'reg_data_{email}'
    data = cache.get(cache_key)
    if data:
        cache.delete(cache_key)  # Delete after retrieval
    return data


def send_password_reset_otp_email(email, otp):
    """Send OTP for password reset"""
    subject = '🔐 E-Gadgets - Password Reset OTP'
    message = f"""
    Hello!
    
    You have requested to reset your password for your E-Gadgets account.
    
    Your OTP for password reset is: {otp}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this, please ignore this email and your password will remain unchanged.
    
    Best regards,
    E-Gadgets Team
    """
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #1e1e1e;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            }}
            .header {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                color: white;
                font-size: 28px;
            }}
            .content {{
                padding: 40px 30px;
                color: #e0e0e0;
            }}
            .otp-box {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                margin: 30px 0;
            }}
            .otp {{
                font-size: 42px;
                font-weight: bold;
                letter-spacing: 8px;
                color: white;
                text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
            }}
            .footer {{
                background: #0d0d0d;
                padding: 20px;
                text-align: center;
                color: #888;
                font-size: 14px;
            }}
            .warning {{
                background: rgba(255, 193, 7, 0.1);
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                color: #ffc107;
            }}
            .info-box {{
                background: rgba(255, 107, 107, 0.1);
                border-left: 4px solid #ff6b6b;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
                color: #ff6b6b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 E-Gadgets</h1>
            </div>
            <div class="content">
                <h2 style="color: #ff6b6b;">Password Reset Request</h2>
                <p>Hello!</p>
                <p>We received a request to reset the password for your E-Gadgets account. Please use the OTP below to proceed with resetting your password:</p>
                
                <div class="otp-box">
                    <div class="otp">{otp}</div>
                </div>
                
                <p style="text-align: center; color: #888;">This OTP is valid for <strong style="color: #ff6b6b;">10 minutes</strong></p>
                
                <div class="info-box">
                    <strong>📝 What happens next:</strong><br>
                    1. Enter this OTP on the password reset page<br>
                    2. Create your new password<br>
                    3. Login with your new credentials
                </div>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong><br>
                    If you didn't request a password reset, please ignore this email. Your password will remain unchanged. Someone may have entered your email address by mistake.
                </div>
            </div>
            <div class="footer">
                <p>© 2025 E-Gadgets. All rights reserved.</p>
                <p>Your one-stop destination for cutting-edge electronics.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False
