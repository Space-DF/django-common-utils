import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from rest_framework.exceptions import ValidationError

client = boto3.client(
    "ses",
    region_name=settings.AWS_S3.get("AWS_REGION"),
    aws_access_key_id=settings.EMAIL_HOST_USER,
    aws_secret_access_key=settings.EMAIL_HOST_PASSWORD,
)


def send_email(sender, user_emails, subject, html_message):
    """Send email via Amazon SES API using boto3."""

    if isinstance(user_emails, str):
        user_emails = [user_emails]

    try:
        response = client.send_email(
            Source=sender,
            Destination={"ToAddresses": user_emails},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_message, "Charset": "UTF-8"},
                    "Text": {
                        "Data": "This email requires an HTML-compatible client.",
                        "Charset": "UTF-8",
                    },
                },
            },
        )
        return response

    except client.exceptions.MessageRejected:
        raise ValidationError({"error": "Email address is not verified."})

    except (BotoCoreError, ClientError) as e:
        raise ValidationError({"error": str(e)})

    except Exception as e:
        raise ValidationError({"error": f"Unexpected Error: {e}"})
