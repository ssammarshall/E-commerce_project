import pytest

@pytest.mark.django_db
class TestCreateCart:
    def test_if_user_is_anonymous_return_200(self, api_client):
        pass