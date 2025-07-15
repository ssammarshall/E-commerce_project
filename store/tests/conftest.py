import pytest

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticate(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    def do_authenticate(is_staff=False):
        from model_bakery import baker
        user = baker.make(User, is_staff=is_staff)
        api_client.force_authenticate(user=user)
        return user
    return do_authenticate
