import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Cart, CartItem, Product

# Fields displayed to User when a CartItem is created.
serializer_create_fields = [
    'id',
    'product_id',
    'quantity',
]

# model_bakery baker does not support AutoSlugField.
# # A generic slug is given to bypass TypeError.
slug = 'product-slug'

def get_cart_items_detail_url(cart_id, item_id):
    from django.urls import reverse
    return reverse('cart-items-detail', kwargs={'cart_pk': cart_id, 'pk': item_id})

def get_cart_items_list_url(cart_id):
    from django.urls import reverse
    return reverse('cart-items-list', kwargs={'cart_pk': cart_id})


# Fixtures.

@pytest.fixture
# Returns tuple of Cart and CartItem.
def cart_and_cart_item():
    cart = baker.make(Cart)
    product = baker.make(Product, slug=slug)
    return (cart, baker.make(CartItem, cart=cart, product_id=product.id))


# Tests.

@pytest.mark.django_db
class TestCreateCartItem: 

    # Validation.
    def test_if_adding_cart_items_with_same_product_updates_and_returns_201(self, api_client):
        # Instead of creating a new CartItem with the same product,
        # update the pre-existing CartItem to the new quantity.
        cart = baker.make(Cart)
        product = baker.make(Product, slug=slug)
        quantity_1 = 3
        cart_item_1 = baker.make(CartItem, cart=cart, product=product, quantity=quantity_1) # cart_item_1
        quantity_2 = 4
        cart_item_2 = {'product_id': product.id, 'quantity': quantity_2}
        url = get_cart_items_list_url(cart.id)

        response = api_client.post(url, cart_item_2)
        data = response.data
        
        assert response.status_code == status.HTTP_201_CREATED
        for field in serializer_create_fields: assert field in data
        assert data['id'] == cart_item_1.id
        assert data['quantity'] == quantity_1 + quantity_2

    def test_if_cart_item_has_invalid_product_id_returns_400(self, api_client):
        cart = baker.make(Cart)
        cart_item = {'product_id': -1, 'quantity': 1}
        url = get_cart_items_list_url(cart.id)

        response = api_client.post(url, cart_item)
        data = response.data
        error = data['product_id'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'No product with given product id was found.'
        assert error.code == 'invalid'

    def test_if_cart_item_quantity_is_less_than_1_returns_400(self, api_client):
        cart = baker.make(Cart)
        product = baker.make(Product, slug=slug)
        cart_item = {'product_id': product.id, 'quantity': 0}
        url = get_cart_items_list_url(cart.id)

        response = api_client.post(url, cart_item)
        data = response.data
        error = data['quantity'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 1.'
        assert error.code == 'min_value'

    # Permissions.
    # CartItems can be created with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        cart = baker.make(Cart)
        product = baker.make(Product, slug=slug)
        quantity = 3
        cart_item = {'product_id': product.id, 'quantity': quantity}
        url = get_cart_items_list_url(cart.id)

        response = api_client.post(url, cart_item)
        data = response.data

        assert response.status_code == status.HTTP_201_CREATED
        for field in serializer_create_fields: assert field in data
        assert data['product_id'] == product.id
        assert data['quantity'] == quantity


@pytest.mark.django_db
class TestDestroyCartItem:

    # Validation.
    def test_if_cart_item_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        cart = baker.make(Cart)
        url = get_cart_items_detail_url(cart.id, -1) # -1 used as garbage value.

        response = api_client.delete(url)
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No CartItem matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    # CartItems can be destroyed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        cart_and_cart_item,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        cart = baker.make(Cart)
        (cart, cart_item) = cart_and_cart_item
        url = get_cart_items_detail_url(cart.id, cart_item.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestListCartItems:
    # TODO: Add pagination

    # Permissions.
    # CartItems can be viewed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        cart = baker.make(Cart)
        num_of_items = 3
        products = baker.make(Product, slug=slug, _quantity=num_of_items)
        for product in products:
            baker.make(CartItem, cart=cart, product=product)
        url = get_cart_items_list_url(cart.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        assert len(data) == num_of_items


@pytest.mark.django_db
class TestPartialUpdateCartItem:

    # Validation.
    def test_if_cart_item_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        cart = baker.make(Cart)
        url = get_cart_items_detail_url(cart.id, -1) # -1 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No CartItem matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    # CartItems can be updated with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        cart = baker.make(Cart)
        product = baker.make(Product, slug=slug)
        original_quantity = 5
        cart_item = baker.make(CartItem, cart=cart, product_id=product.id, quantity=original_quantity)
        new_quantity = 10
        payload = {'quantity': new_quantity}
        url = get_cart_items_detail_url(cart.id, cart_item.id)

        response = api_client.patch(url, payload)
        data = response.data
    
        assert response.status_code == status.HTTP_200_OK
        assert data['quantity'] == new_quantity


@pytest.mark.django_db
class TestRetrieveCartItem:

    # Validation.
    def test_if_cart_item_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        cart = baker.make(Cart)
        url = get_cart_items_detail_url(cart.id, -1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No CartItem matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    # CartItems can be viewed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        cart_and_cart_item,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        cart = baker.make(Cart)
        (cart, cart_item) = cart_and_cart_item
        url = get_cart_items_detail_url(cart.id, cart_item.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        assert data['product'] # Returns the Product object, not just 'product_id'


@pytest.mark.django_db
class TestUpdateCartItem:

    # No validation. Method not allowed.

    # Permissions.
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        cart = baker.make(Cart)
        product = baker.make(Product, slug=slug)
        cart_item = baker.make(CartItem, cart=cart, product_id=product.id)

        url = get_cart_items_detail_url(cart.id, cart_item.id)

        response = api_client.put(url, {})
        data = response.data
    
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
