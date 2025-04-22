from datetime import timedelta

from rest_framework_simplejwt.tokens import AccessToken


def generate_token(data, exp=15):
    token = AccessToken()
    token.set_exp(lifetime=timedelta(minutes=exp))

    for key, value in data.items():
        token[key] = value

    return str(token)
