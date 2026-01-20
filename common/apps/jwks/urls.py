from django.urls import path

from common.apps.jwks.views import JWKView

app_name = "jwks"

urlpatterns = [
    path(".well-known/jwks.json", JWKView.as_view(), name="jwks"),
]
