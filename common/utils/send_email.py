import re

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


def send_email(sender, user_emails, subject, html_message, text_message=None, reply_to=None):
    """Send email via Amazon SES API using boto3."""

    if isinstance(user_emails, str):
        user_emails = [user_emails]

    if text_message is None:
        text_message = _html_to_plain_text(html_message)

    kwargs = {
        "Source": sender,
        "Destination": {"ToAddresses": user_emails},
        "Message": {
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Html": {"Data": html_message, "Charset": "UTF-8"},
                "Text": {"Data": text_message, "Charset": "UTF-8"},
            },
        },
    }

    if reply_to:
        kwargs["ReplyToAddresses"] = [reply_to] if isinstance(reply_to, str) else reply_to

    try:
        response = client.send_email(**kwargs)
        return response

    except client.exceptions.MessageRejected:
        raise ValidationError({"error": "Email address is not verified."})

    except (BotoCoreError, ClientError) as e:
        raise ValidationError({"error": str(e)})

    except Exception as e:
        raise ValidationError({"error": f"Unexpected Error: {e}"})


def _html_to_plain_text(html):
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n\n", text)
    text = re.sub(r"<a[^>]*href=\"([^\"]+)\"[^>]*>[^<]*</a>", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
