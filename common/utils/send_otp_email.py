import secrets
import smtplib
import string

from django.core.cache import cache  # Import Django's Redis cache
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

OTP_EXPIRY_SECONDS = 600  # 10 minutes


def generate_otp(length=6):
    """Generate a 6-digit OTP."""
    return "".join(secrets.choice(string.digits) for _ in range(length))


def send_otp_email(sender, user_email):
    """Send OTP to user and store it in Redis."""
    try:
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

        send_mail(subject, message, sender, [user_email])

        return otp_code

    except smtplib.SMTPDataError:
        raise ValidationError({"error": "Email address is not verified."})

    except smtplib.SMTPException as e:
        raise ValidationError({"error": str(e)})

    except Exception as e:
        raise ValidationError({"error": f"Unexpected Error: {e}"})
