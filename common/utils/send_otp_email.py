import secrets
import string

from django.conf import settings
from django.core.cache import cache  # Import Django's Redis cache
from django.core.mail import send_mail

OTP_EXPIRY_SECONDS = 600  # 10 minutes


def generate_otp(length=6):
    """Generate a 6-digit OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def send_otp_email(user_email):
    """Send OTP to user and store it in Redis."""
    otp_code = generate_otp()

    # Store OTP in Redis with a 10-minute expiration
    cache.set(f"otp_{user_email}", otp_code, timeout=OTP_EXPIRY_SECONDS)

    # Email content
    subject = "Your One-Time Sign-In Code"
    message = f"""
    Hello,

    Your one-time sign-in code is: {otp_code}

    This code will expire in 10 minutes.

    Best regards,
    Digital Fortress
    """

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])

    return otp_code
