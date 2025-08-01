import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Customer, Order, OrderItem, Product

# Fields displayed to User when a OrderItem is created.
serializer_create_fields = [
    'id',
    'product_id',
    'quantity',
]
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
    
    # Validation.
    def test_if_adding_order_items_with_same_product_updates_and_returns_201(self, api_client, authenticate, order_and_order_item):
        # Instead of creating a new OrderItem with the same product,
        # update the pre-existing CartItOrderItemem to the new quantity.
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        product = baker.make(Product, slug=slug)
        quantity_1 = 3
        order_item_1 = baker.make(OrderItem, order=order, product=product, quantity=quantity_1)
        quantity_2 = 4
        order_item_2 = {'product_id': product.id, 'quantity': quantity_2}
        url = get_order_items_list_url(order.id)

        response = api_client.post(url, order_item_2)
        data = response.data
        
        assert response.status_code == status.HTTP_201_CREATED
        for field in serializer_create_fields: assert field in data
        assert data['id'] == order_item_1.id
        assert data['quantity'] == quantity_1 + quantity_2

    def test_if_order_item_has_invalid_product_id_returns_400(self, api_client, authenticate, order_and_order_item):
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        order_item = {'product_id': -1, 'quantity': 1}
        url = get_order_items_list_url(order.id)

        response = api_client.post(url, order_item)
        data = response.data
        error = data['product_id'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'No product with given product id was found.'
        assert error.code == 'invalid'

    def test_if_cart_item_quantity_is_less_than_1_returns_400(self, api_client, authenticate, order_and_order_item):
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        product = baker.make(Product, slug=slug)
        order_item = {'product_id': product.id, 'quantity': 0}
        url = get_order_items_list_url(order.id)

        response = api_client.post(url, order_item)
        data = response.data
        error = data['quantity'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 1.'
        assert error.code == 'min_value'


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
        order_and_order_item,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            (order, _order_item) = order_and_order_item(user=user)
        else: (order, _order_item) = order_and_order_item()
        product = baker.make(Product, slug=slug)
        quantity = 6
        order_item = {'product_id': product.id, 'quantity': quantity}
        url = get_order_items_list_url(order.id)

        response = api_client.post(url, order_item)
        data = response.data

        assert response.status_code == expected
        if is_staff is not None:
            for field in serializer_create_fields: assert field in data
            assert data['product_id'] == product.id
            assert data['quantity'] == quantity


@pytest.mark.django_db
class TestDestroyOrderItem:

    # Validation.
    def test_if_order_item_does_not_exist_returns_404(self, api_client, authenticate, order_and_order_item):
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
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

    # Filter Backends.
    def test_if_list_can_order_by_product_price(self, api_client, authenticate, order_and_order_item):
        from decimal import Decimal
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        num_of_additional_items = 5
        for i in range(num_of_additional_items):
            product = baker.make(Product, slug=slug)
            baker.make(OrderItem, order=order, product_id=product.id)

        # Ascending order.
        url = get_order_items_list_url(order.id) + '?ordering=product__price'

        response = api_client.get(url)
        data = response.data
        results = data['results']
        
        prices_ascending = [Decimal(item['product']['price']) for item in results]
        
        assert response.status_code == status.HTTP_200_OK
        assert prices_ascending == sorted(prices_ascending)
        
        # Descending order.
        url = get_order_items_list_url(order.id) + '?ordering=-product__price'

        response = api_client.get(url)
        data = response.data
        results = data['results']
        prices_descending = [Decimal(item['product']['price']) for item in results]

        assert response.status_code == status.HTTP_200_OK
        assert prices_descending == sorted(prices_descending, reverse=True)

    def test_if_list_can_order_by_quantity(self, api_client, authenticate, order_and_order_item):
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        num_of_additional_items = 5
        for i in range(num_of_additional_items):
            product = baker.make(Product, slug=slug)
            baker.make(OrderItem, order=order, product_id=product.id)

        # Ascending order.
        url = get_order_items_list_url(order.id) + '?ordering=quantity'

        response = api_client.get(url)
        data = response.data
        results = data['results']
        
        quantity_ascending = [item['quantity'] for item in results]
        
        assert response.status_code == status.HTTP_200_OK
        assert quantity_ascending == sorted(quantity_ascending)
        
        # Descending order.
        url = get_order_items_list_url(order.id) + '?ordering=-quantity'

        response = api_client.get(url)
        data = response.data
        results = data['results']
        quantity_descending = [item['quantity'] for item in results]

        assert response.status_code == status.HTTP_200_OK
        assert quantity_descending == sorted(quantity_descending, reverse=True)

    def test_if_list_has_pagination_present(self, api_client, authenticate, order_and_order_item):
        from store.pagination import DefaultPagination
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        max_num_of_pages = DefaultPagination.page_size
        products = baker.make(Product, slug=slug, _quantity=max_num_of_pages+1)
        for product in products:
            baker.make(OrderItem, order=order, product_id=product.id)
        url = get_order_items_list_url(order.id)

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert data['next'] != None
        assert data['previous'] == None
        assert data['results']
        assert len(data['results']) == max_num_of_pages

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
            assert data['results'][0]['id'] == order_item.id


@pytest.mark.django_db
class TestPartialUpdateOrderItem:
    
    # Validation.
    def test_if_order_item_does_not_exist_returns_404(self, api_client, authenticate, order_and_order_item):
        user = authenticate(True)
        (order, _order_item) = order_and_order_item(user=user)
        url = get_order_items_detail_url(order.id, -1) # -1 used as garbage value.

        response = api_client.patch(url, {})
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
        original_quantity = order_item.quantity
        new_quantity = original_quantity + 1
        payload = {'quantity': new_quantity}
        url = get_order_items_detail_url(order.id, order_item.id)

        response = api_client.patch(url, payload)
        data = response.data
        
        assert response.status_code == expected
        if is_staff is not None:
            assert data['quantity'] == new_quantity


@pytest.mark.django_db
class TestRetrieveOrderItem:

    # Validation.
    def test_if_order_item_does_not_exist_returns_404(self, api_client, authenticate, order_and_order_item):
        authenticate(True)
        (order, _order_item) = order_and_order_item()
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
        order_and_order_item,
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            (order, order_item) = order_and_order_item(user=user)
        else: (order, order_item) = order_and_order_item()
        url = get_order_items_detail_url(order.id, order_item.id)

        response = api_client.put(url, {})

        assert response.status_code == expected
