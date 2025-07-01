import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Cart

# Fixtures.

@pytest.fixture
def create_cart(api_client):
    def do_create_cart(cart):
        return api_client.post('/store/carts/', cart)
    return do_create_cart


@pytest.mark.django_db
class TestCreateCart:
    def test_if_user_is_anonymous_returns_201(self, create_cart):
        # Carts can be created without Customer/User profile.
        response = create_cart({})

        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestRetrieveCart:
    def test_if_cart_exists_returns_200(self, api_client):
        cart = baker.make(Cart)

        response = api_client.get(f'/store/carts/{cart.id}/')

        assert response.status_code == status.HTTP_200_OK
    
    def test_if_cart_does_not_exist_returns_404(self, api_client):
        # CartModel declares primary_key as UUIDField.
        # UUIDField is represented as a 36-character string with hyphens.
        # A single character to be used for UUIDField will always fail.
        response = api_client.get('/store/carts/a/') # 'a' used as garbage value.

        assert response.status_code == status.HTTP_404_NOT_FOUND
