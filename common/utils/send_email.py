import smtplib

from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError


def send_email(sender, user_email, subject, message):
    """Send email to user and store it in Redis."""
    try:
        send_mail(
            subject=subject,
            message="",
            from_email=sender,
            recipient_list=user_email,
            html_message=message,
            fail_silently=False,
        )

    except smtplib.SMTPDataError:
        raise ValidationError({"error": "Email address is not verified."})

    except smtplib.SMTPException as e:
        raise ValidationError({"error": str(e)})

    except Exception as e:
        raise ValidationError({"error": f"Unexpected Error: {e}"})
