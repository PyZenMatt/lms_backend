import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.conf import settings

User = get_user_model()

@pytest.mark.django_db
def test_refresh_includes_role_claim(settings):
    # create a user with admin role
    u = User.objects.create_user(email="admin@example.com", password="pass", role="admin", username="admin")
    refresh = RefreshToken.for_user(u)

    client = APIClient()
    url = reverse("token_refresh")  # this is namespaced in authentication.urls
    resp = client.post(url, {"refresh": str(refresh)}, format="json")
    assert resp.status_code == 200, resp.content
    data = resp.json()
    assert "access" in data
    token = data["access"]
    # decode without verification to inspect payload
    payload = jwt.decode(token, options={"verify_signature": False})
    # also exercise serializer directly to ensure code path
    from authentication.serializers import CustomTokenRefreshSerializer
    s = CustomTokenRefreshSerializer(data={"refresh": str(refresh)})
    # avoid s.is_valid() since it performs blacklist verification; call validate directly
    try:
        validated = s.validate({"refresh": str(refresh)})
    except Exception as e:
        validated = {}
        ser_error = str(e)
    ser_access = validated.get("access")
    ser_payload = jwt.decode(ser_access, options={"verify_signature": False}) if ser_access else {}
    # include both payloads in failure message to debug why role missing
    msg = f"response payload missing role; payload={payload}; serializer_payload={ser_payload}"
    if 'ser_error' in locals():
        msg += f"; serializer_error={ser_error}"
    assert payload.get("role") == "admin", msg
