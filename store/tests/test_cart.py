import pytest
from rest_framework import status
@pytest.mark.django_db
class TestCreateCart:
    def test_if_user_is_anonymous_return_403(self, api_client):
        response = api_client.post('/store/collections/', {'title': 'a'})
        assert response.status_code == status.HTTP_403_FORBIDDEN