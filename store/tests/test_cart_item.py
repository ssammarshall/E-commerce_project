import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Cart, CartItem, Product

# Fixtures.

@pytest.fixture
def create_cart_item(api_client):
    def do_create_cart_item(cart, cart_item):
        return api_client.post(f'/store/carts/{cart.id}/items/', cart_item)
    return do_create_cart_item


@pytest.mark.django_db
class TestCreateCartItem:
    def test_if_add_cart_item_to_cart_returns_201(self, create_cart_item):
        cart = baker.make(Cart)
        product = baker.make(Product, slug='product-slug')

        response = create_cart_item(cart, {'cart': cart, 'product': product, 'quantity': 1})

        assert response.status_code == status.HTTP_201_CREATED