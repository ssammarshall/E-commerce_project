import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Cart, CartItem, Customer, Order, Product

# Fields displayed to User when a Order is returned.
serializer_fields = [
    'id',
    'payment_status',
    'placed_at',
    'items',
    'total_price'
]

# model_bakery baker does not support PhoneNumberField.
# A generic number is given to bypass TypeError.
phone_number = '+18005551234'

def get_order_detail_url(id):
    from django.urls import reverse
    return reverse('orders-detail', kwargs={'pk': id})

def get_order_list_url():
    from django.urls import reverse
    return reverse('orders-list')

def create_order_payload(cart, user=None, num_of_items=3):
    if user is not None:
        baker.make(Customer, user=user, phone_number=phone_number)
    if num_of_items > 0:
        products = baker.make(Product, slug='slug', _quantity=num_of_items)
        for product in products:
            baker.make(CartItem, cart=cart, product=product)
    payload = {'cart_id': cart.id}
    return payload


# Fixtures.

@pytest.fixture
# Return an Order for a pre-existing Customer.
def order_for_customer():
    def get_order_for_customer(user=None):
        if user is not None: customer = baker.make(Customer, user=user, phone_number=phone_number)
        else: customer = baker.make(Customer, phone_number=phone_number)
        return baker.make(Order, customer=customer)
    return get_order_for_customer


# Tests.

@pytest.mark.django_db
class TestCreateOrder:
    # TODO: remove Cart.DoesNotExist exception in OrderPostSerializer.create()

    # Validation.
    def test_if_empty_cart_returns_400(self, api_client, authenticate):
        user = authenticate(True)
        cart = baker.make(Cart)
        payload = create_order_payload(cart, user=user, num_of_items=0)
        url = get_order_list_url()

        response = api_client.post(url, payload)
        data = response.data
        error = data[0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'No items found in cart. Cannot create an empty order.'
        assert error.code == 'invalid'

    def test_if_no_customer_profile_returns_400(self, api_client, authenticate):
        authenticate(True)
        cart = baker.make(Cart)
        payload = create_order_payload(cart)
        url = get_order_list_url()

        response = api_client.post(url, payload)
        data = response.data
        error = data[0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'No customer with given user id was found.'
        assert error.code == 'invalid'

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_201_CREATED),
        (True, status.HTTP_201_CREATED)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            cart = baker.make(Cart)
            payload = create_order_payload(cart, user=user)
        else:
            cart = baker.make(Cart)
            payload = create_order_payload(cart)
        url = get_order_list_url()

        response = api_client.post(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestDestroyOrder:
    # TODO: Cancel Orders

    # No validation. Method not allowed.

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_403_FORBIDDEN),
        (True, status.HTTP_405_METHOD_NOT_ALLOWED)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        order_for_customer,
        is_staff,
        expected
    ):
        if is_staff is not None:
            authenticate(is_staff)
        order = order_for_customer()        
        url = get_order_detail_url(order.id)

        response = api_client.delete(url)
    
        assert response.status_code == expected


@pytest.mark.django_db
class TestListOrder:
    # TODO: Auth users should only see their orders. Admin can see all
    # TODO: Add pagination and order by placed_at

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_200_OK),
        (True, status.HTTP_200_OK)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        order_for_customer,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            order = order_for_customer(user=user)
        url = get_order_list_url()

        response = api_client.get(url)
        data = response.data

        assert response.status_code == expected
        if is_staff is not None:
            assert data[0]['id'] == order.id


@pytest.mark.django_db
class TestPartialUpdateOrder:

    # Validation.
    def test_if_order_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_order_detail_url(-1) # -1 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Order matches the given query.'
        assert error.code == 'not_found'
    
    def test_if_invalid_payment_status_returns_400(self, api_client, authenticate, order_for_customer):
        authenticate(True)
        order = order_for_customer()
        choice = 'Q'
        payload = {'payment_status': choice}
        url = get_order_detail_url(order.id)

        response = api_client.patch(url, payload, format='json')
        data = response.data
        error = data['payment_status'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == f'"{choice}" is not a valid choice.'
        assert error.code == 'invalid_choice'

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_403_FORBIDDEN),
        (True, status.HTTP_200_OK)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        order_for_customer,
        is_staff,
        expected
    ):
        if is_staff is not None:
            authenticate(is_staff)
        order = order_for_customer()
        if order.payment_status == 'P': payload = {'payment_status': 'C'}
        else: payload = {'payment_status': 'P'}
        url = get_order_detail_url(order.id)

        response = api_client.patch(url, payload, format='json')
        data = response.data

        assert response.status_code == expected
        if is_staff:
            assert data['payment_status'] == payload['payment_status']


@pytest.mark.django_db
class TestRetrieveOrder:
    
    # Validation.
    def test_if_order_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_order_detail_url(-1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Order matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_200_OK),
        (True, status.HTTP_200_OK)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        order_for_customer,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            order = order_for_customer(user=user)
        else: order = order_for_customer()
        url = get_order_detail_url(order.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == expected
        if is_staff is None:
            assert data['detail'] == 'Authentication credentials were not provided.'
            assert data['detail'].code == 'not_authenticated'
        else:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestUpdateOrder:

    # No validation. Method not allowed.

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_405_METHOD_NOT_ALLOWED),
        (True, status.HTTP_405_METHOD_NOT_ALLOWED)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        order_for_customer,
        is_staff,
        expected
    ):
        if is_staff is not None:
            authenticate(is_staff)
        order = order_for_customer()
        if order.payment_status == 'P': payload = {'payment_status': 'C'}
        else: payload = {'payment_status': 'P'}
        url = get_order_detail_url(order.id)

        response = api_client.put(url, payload, format='json')

        assert response.status_code == expected
