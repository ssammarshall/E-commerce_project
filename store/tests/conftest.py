import pytest

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticate(api_client):
    from django.contrib.auth import get_user_model
    def do_authenticate(is_staff=False):
        user = get_user_model()
        return api_client.force_authenticate(user=user(is_staff=is_staff))
    return do_authenticate