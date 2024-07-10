from common.apps.jwks.views import JWKView
from django.urls import path

app_name = "jwks"

urlpatterns = [
    path(".well-known/jwks.json", JWKView.as_view(), name="jwks"),
]
