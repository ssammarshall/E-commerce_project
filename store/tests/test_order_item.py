import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Customer, Order, OrderItem, Product

# Fields displayed to User when a OrderItem is returned.
serializer_fields = [
    'id',
    'product',
    'quantity',
    'total_price'
]

# model_bakery baker does not support AutoSlugField or PhoneNumberField.
# # A generic slug and number is given to bypass TypeError.
phone_number = '+18005551234'
slug = 'product-slug'

def get_order_items_detail_url(order_id, item_id):
    from django.urls import reverse
    return reverse('order-items-detail', kwargs={'order_pk': order_id, 'pk': item_id})

def get_order_items_list_url(order_id):
    from django.urls import reverse
    return reverse('order-items-list', kwargs={'order_pk': order_id})


# Fixtures.

@pytest.fixture
# Returns tuple of Order and OrderItem.
def order_and_order_item():
    def get_order_and_order_item(user=None):
        if user is not None: customer = baker.make(Customer, user=user, phone_number=phone_number)
        else: customer = baker.make(Customer, phone_number=phone_number)
        order = baker.make(Order, customer=customer)
        product = baker.make(Product, slug=slug)
        return (order, baker.make(OrderItem, order=order, product_id=product.id))
    return get_order_and_order_item


# Tests.

@pytest.mark.django_db
class TestCreateOrderItem:
    # TODO: Either do not allow post requests or create OrderItemPostSerializer
    pass


@pytest.mark.django_db
class TestDestroyOrderItem:

    # Validation.
    def test_if_order_item_does_not_exist_returns_404(self, api_client, authenticate, order_and_order_item):
        user = authenticate(True)
        (order, order_item) = order_and_order_item()
        url = get_order_items_detail_url(order.id, -1)

        response = api_client.delete(url)
        data = response.data
        error = data['detail']
 
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No OrderItem matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_204_NO_CONTENT),
        (True, status.HTTP_204_NO_CONTENT)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        order_and_order_item,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            (order, order_item) = order_and_order_item(user=user) 
        else:
            (order, order_item) = order_and_order_item()       
        url = get_order_items_detail_url(order.id, order_item.id)

        response = api_client.delete(url)
    
        assert response.status_code == expected


@pytest.mark.django_db
class TestListOrderItem:
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
        order_and_order_item,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            (order, order_item) = order_and_order_item(user=user)
        else: (order, order_item) = order_and_order_item()
        url = get_order_items_list_url(order.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == expected
        if is_staff is not None:
            assert data[0]['id'] == order_item.id


@pytest.mark.django_db
class TestPartialUpdateOrderItem:
    pass # TODO: OrderItemPatchSerializer


@pytest.mark.django_db
class TestRetrieveOrderItem:

    # Validation.
    def test_if_order_item_does_not_exist_returns_404(self, api_client, authenticate, order_and_order_item):
        authenticate(True)
        (order, order_item) = order_and_order_item()
        url = get_order_items_detail_url(order.id, -1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No OrderItem matches the given query.'
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
        order_and_order_item,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            (order, order_item) = order_and_order_item(user=user)
        else: (order, order_item) = order_and_order_item()
        url = get_order_items_detail_url(order.id, order_item.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == expected
        if is_staff is None:
            assert data['detail'] == 'Authentication credentials were not provided.'
            assert data['detail'].code == 'not_authenticated'
        else:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestUpdateOrderItem:
    pass # TODO: Do not allow put in OrderItemViewSet