import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Cart

# Fields displayed to User when a Cart is returned.
serializer_fields = [
    'id',
    'created_at',
    'items',
    'total_price'
]

def get_cart_detail_url(id):
    from django.urls import reverse
    return reverse('cart-detail', kwargs={'pk': id})

def get_cart_list_url():
    from django.urls import reverse
    return reverse('cart-list')


# Tests.

@pytest.mark.django_db
class TestCreateCart:

    # Permissions.
    # Carts can be created with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        url = get_cart_list_url()

        response = api_client.post(url, {}) # Empty Cart.
        data = response.data

        assert response.status_code == status.HTTP_201_CREATED
        for field in serializer_fields: assert field in data
        assert data['items'] == [] # Empty Cart.


@pytest.mark.django_db
class TestDestroyCart:

    # Validation.
    def test_if_cart_does_not_exist_returns_404(self, api_client, authenticate):
        import uuid
        authenticate(True)
        url = get_cart_detail_url(uuid.uuid4) # Random uuid4 used as garbage value.

        response = api_client.delete(url)
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'Not found.'
        assert error.code == 'not_found'

    # Permissions.
    # Carts can be destroyed with or without authentication (Customer/User profile).
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
        url = get_cart_detail_url(cart.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestListCart:
    pass # TODO: Remove functionality of listing all carts and require a cart to be specified. Test this returns 403


@pytest.mark.django_db
class TestPartialUpdateCart:

     # Validation.
    def test_if_cart_does_not_exist_returns_404(self, api_client, authenticate):
        import uuid
        authenticate(True)
        url = get_cart_detail_url(uuid.uuid4) # Random uuid4 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'Not found.'
        assert error.code == 'not_found'

    # Permissions.
    # Carts can be updated with or without authentication (Customer/User profile).
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
        url = get_cart_detail_url(cart.id)

        response = api_client.patch(url, {})
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestRetrieveCart:

    # Validation.
    def test_if_cart_does_not_exist_returns_404(self, api_client, authenticate):
        import uuid
        authenticate(True)
        url = get_cart_detail_url(uuid.uuid4) # Random uuid4 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'Not found.'
        assert error.code == 'not_found'
    
    # Permissions.
    # Carts can be viewed with or without authentication (Customer/User profile).
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
        url = get_cart_detail_url(cart.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestUpdateCart:

    # Validation.
    def test_if_cart_does_not_exist_returns_404(self, api_client, authenticate):
        import uuid
        authenticate(True)
        url = get_cart_detail_url(uuid.uuid4) # Random uuid4 used as garbage value.

        response = api_client.put(url, {})
        data = response.data
        error = data['detail']
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'Not found.'
        assert error.code == 'not_found'

    # Permissions.
    # Carts can be updated with or without authentication (Customer/User profile).
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
        url = get_cart_detail_url(cart.id)

        response = api_client.put(url, {})
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        for field in serializer_fields: assert field in data
