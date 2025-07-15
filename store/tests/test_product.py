import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Collection, Product

# Fields displayed to User when a Product is returned.
serializer_fields = [
    'id',
    'title',
    'price',
    'description',
    'inventory',
    'collection'
]

# model_bakery baker does not support AutoSlugField.
# # A generic slug is given to bypass TypeError.
slug = 'product-slug'

def get_products_detail_url(id):
    from django.urls import reverse
    return reverse('products-detail', kwargs={'pk': id})

def get_products_list_url():
    from django.urls import reverse
    return reverse('products-list')

def create_product_payload(collection_id, **overrides):
    payload = {
        'title': 'T',
        'price': '1.00',
        'description': 'D',
        'inventory': 1,
        'collection': collection_id
    }
    payload.update(overrides)
    return payload


# Tests.

@pytest.mark.django_db
class TestCreateProduct:

    # Validation.
    MISSING_FIELD_PAYLOADS = [
        ('title', {'price': '1.00', 'description': 'D', 'inventory': 1, 'collection': 1}),
        ('price', {'title': 'T', 'description': 'D', 'inventory': 1, 'collection': 1}),
        ('description', {'title': 'T', 'price': '1.00', 'inventory': 1, 'collection': 1}),
        ('inventory', {'title': 'T', 'price': '1.00', 'description': 'D', 'collection': 1}),
        ('collection', {'title': 'T', 'price': '1.00', 'description': 'D', 'inventory': 1}),
    ]
    @pytest.mark.parametrize('missing_field, payload', MISSING_FIELD_PAYLOADS)
    def test_if_missing_required_field_returns_400(
        self, 
        api_client, 
        authenticate, 
        missing_field,
        payload
    ):
        authenticate(True)
        url = get_products_list_url()

        response = api_client.post(url, payload)
        data = response.data
        error = data[missing_field][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'This field is required.'
        assert error.code == 'required'

    def test_if_inventory_less_than_0_returns_400(self, api_client, authenticate):
        authenticate(True)
        collection = baker.make(Collection)
        payload = create_product_payload(collection_id=collection.id, inventory=-1)
        url = get_products_list_url()

        response = api_client.post(url, payload)
        data = response.data
        error = data['inventory'][0]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 0.'
    
    def test_if_price_less_than_1_returns_400(self, api_client, authenticate):
        authenticate(True)
        collection = baker.make(Collection)
        payload = create_product_payload(collection_id=collection.id, price='0.00')
        url = get_products_list_url()

        response = api_client.post(url, payload)
        data = response.data
        error = data['price'][0]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 1.'
    
    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_403_FORBIDDEN),
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
        if is_staff is not None: authenticate(is_staff)
        collection = baker.make(Collection)
        payload = create_product_payload(collection.id)
        url = get_products_list_url()

        response = api_client.post(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestDestoryProduct:

    # Validation.
    def test_if_product_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_products_detail_url(-1) # -1 used as garbage value.

        response = api_client.delete(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Product matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    EXPECTED_PERMISSION_CLASS_RESPONSES = [
        (None, status.HTTP_403_FORBIDDEN),
        (False, status.HTTP_403_FORBIDDEN),
        (True, status.HTTP_204_NO_CONTENT)
    ]
    @pytest.mark.parametrize('is_staff, expected', EXPECTED_PERMISSION_CLASS_RESPONSES)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
        expected
    ):
        if is_staff is not None: authenticate(is_staff)
        product = baker.make(Product, slug=slug)
        url = get_products_detail_url(product.id)

        response = api_client.delete(url)

        assert response.status_code == expected


@pytest.mark.django_db
class TestListProduct:

    # Filter Backends.
    def test_if_list_can_filter_by_collection(self, api_client):
        collection1 = baker.make(Collection)
        collection1_num_of_products = 5
        baker.make(Product, slug=slug, collection=collection1, _quantity=collection1_num_of_products)
        collection2 = baker.make(Collection)
        collection2_num_of_products = 6
        baker.make(Product, slug=slug, collection=collection2, _quantity=collection2_num_of_products)
        url = get_products_list_url() + f'?collection_id={collection1.id}'

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert data['results']
        assert len(data['results']) == collection1_num_of_products

    def test_if_list_can_filter_by_price(self, api_client):
        from decimal import Decimal
        # Greater than.
        high_price = 30.00
        num_of_expensive_products = 5
        baker.make(Product, slug=slug, price=high_price + 0.01, _quantity=num_of_expensive_products) # Products with a price $0.01 more than low_price.
        baker.make(Product, slug=slug, price=high_price - 0.01, _quantity=100) # Products with a price $0.01 less than low_price.
        url = get_products_list_url() + f'?price__gt={high_price}'

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert len(data['results']) == num_of_expensive_products
        for product in data['results']: assert Decimal(product['price']) > high_price

        # Less than.
        low_price = 3.00
        num_of_cheap_products = 4
        baker.make(Product, slug=slug, price=low_price - 0.01, _quantity=num_of_cheap_products) # Products with a price $0.01 less than low_price.
        baker.make(Product, slug=slug, price=low_price + 0.01, _quantity=100) # Products with a price $0.01 more than low_price.
        url = get_products_list_url() + f'?price__lt={low_price}'

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert len(data['results']) == num_of_cheap_products
        for product in data['results']: assert Decimal(product['price']) < low_price

    def test_if_list_can_order_by_last_update(self, api_client):
        # JSON data from response does not contain the last_update field.
        # The last_update field is set to auto_now=True, therefore last_update
        # ordering can be evaluated by product.id since the Products are
        # created then immediately retrieved by the APIClient.

        # Ascending order.
        baker.make(Product, slug=slug, _quantity=5)
        url = get_products_list_url() + '?ordering=last_update'

        response = api_client.get(url)
        data = response.data
        update_times_ascending = [(item['id']) for item in data.get('results', data)]

        assert response.status_code == status.HTTP_200_OK
        assert update_times_ascending == sorted(update_times_ascending)

        # Descending order.
        url = get_products_list_url() + '?ordering=-last_update'

        response = api_client.get(url)
        data = response.data
        update_times_descending = [(item['id']) for item in data.get('results', data)]

        assert response.status_code == status.HTTP_200_OK
        assert update_times_descending == sorted(update_times_descending, reverse=True)

    def test_if_list_can_order_by_price(self, api_client):
        from decimal import Decimal
        # Ascending order.
        baker.make(Product, slug=slug, _quantity=5)
        url = get_products_list_url() + '?ordering=price'

        response = api_client.get(url)
        data = response.data
        prices_ascending = [Decimal(item['price']) for item in data.get('results', data)]

        assert response.status_code == status.HTTP_200_OK
        assert prices_ascending == sorted(prices_ascending)
        
        # Descending order.
        url = get_products_list_url() + '?ordering=-price'

        response = api_client.get(url)
        data = response.data
        prices_descending = [Decimal(item['price']) for item in data.get('results', data)]

        assert response.status_code == status.HTTP_200_OK
        assert prices_descending == sorted(prices_descending, reverse=True)

    def test_if_list_can_order_by_title(self, api_client):
        # Ascending order.
        baker.make(Product, slug=slug, _quantity=5)
        url = get_products_list_url() + '?ordering=title'

        response = api_client.get(url)
        data = response.data
        results = data['results']
        titles_ascending = [product['title'] for product in results]
        
        assert response.status_code == status.HTTP_200_OK
        assert titles_ascending == sorted(titles_ascending, key=str.lower)
        
        # Descending order.
        url = get_products_list_url() + '?ordering=-title'

        response = api_client.get(url)
        data = response.data
        results = data['results']
        titles_descending = [product['title'] for product in results]

        assert response.status_code == status.HTTP_200_OK
        assert titles_descending == sorted(titles_descending, key=str.lower, reverse=True)

    def test_if_list_can_search_by_title(self, api_client):
        search_text = 'Big'
        title1 = search_text + ' Truck'
        baker.make(Product, title=title1, slug=slug)
        title2 = 'Small Boat'
        baker.make(Product, title=title2, slug=slug)
        url = get_products_list_url() + f'?search={search_text}'

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert data['results']
        assert len(data['results']) == 1
        assert data['results'][0]['title'] == title1

    def test_if_list_has_pagination_present(self, api_client):
        from store.pagination import DefaultPagination
        max_num_of_pages = DefaultPagination.page_size
        baker.make(Product, slug=slug, _quantity=max_num_of_pages+1)
        url = get_products_list_url()

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert data['next'] != None
        assert data['previous'] == None
        assert data['results']
        assert len(data['results']) == max_num_of_pages

    # Permissions.
    # Products can be viewed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        num_of_products = 5
        baker.make(Product, slug=slug, _quantity=num_of_products)
        url = get_products_list_url()

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        assert len(data['results']) == num_of_products


@pytest.mark.django_db
class TestPartialUpdateProduct:

    # Validation.
    def test_if_product_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_products_detail_url(-1) # -1 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Product matches the given query.'
        assert error.code == 'not_found'

    def test_if_inventory_less_than_0_returns_400(self, api_client, authenticate):
        authenticate(True)
        product = baker.make(Product, slug=slug)

        new_inventory = -1 # -1 used as garbage value.
        payload = {'inventory': new_inventory}
        url = get_products_detail_url(product.id)

        response = api_client.patch(url, payload)
        data = response.data
        error = data['inventory'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 0.'
        assert error.code == 'min_value'
    
    def test_if_price_less_than_1_returns_400(self, api_client, authenticate):
        authenticate(True)
        product = baker.make(Product, slug=slug)
        new_price = '0.00' # '0.00' used as garbage value.
        payload = {'price': new_price}
        url = get_products_detail_url(product.id)

        response = api_client.patch(url, payload)
        data = response.data
        error = data['price'][0]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 1.'
        assert error.code == 'min_value'

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
        is_staff,
        expected
    ):
        if is_staff is not None: authenticate(is_staff)
        product = baker.make(Product, slug=slug)
        new_title = 'new title'
        payload = {'title': new_title}
        url = get_products_detail_url(product.id)

        response = api_client.patch(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data
            assert data['title'] == new_title


@pytest.mark.django_db
class TestRetrieveProduct:

    # Validation.
    def test_if_product_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_products_detail_url(-1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Product matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    # Products can be viewed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        product = baker.make(Product, slug=slug)
        url = get_products_detail_url(product.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestUpdateProduct:

    # Validation.
    def test_if_product_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_products_detail_url(-1) # -1 used as garbage value.

        response = api_client.put(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Product matches the given query.'
        assert error.code == 'not_found'

    def test_if_inventory_less_than_0_returns_400(self, api_client, authenticate):
        authenticate(True)
        product = baker.make(Product, slug=slug)
        collection = baker.make(Collection)
        new_inventory = -1 # -1 used as garbage value.
        payload = create_product_payload(collection_id=collection.id, inventory=new_inventory)
        url = get_products_detail_url(product.id)

        response = api_client.patch(url, payload)
        data = response.data
        error = data['inventory'][0]
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 0.'
        assert error.code == 'min_value'
    
    def test_if_price_less_than_1_returns_400(self, api_client, authenticate):
        authenticate(True)
        product = baker.make(Product, slug=slug)
        collection = baker.make(Collection)
        new_price = '0.00' # '0.00' used as garbage value.
        payload = create_product_payload(collection_id=collection.id, price=new_price)
        url = get_products_detail_url(product.id)

        response = api_client.put(url, payload)
        data = response.data
        error = data['price'][0]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'Ensure this value is greater than or equal to 1.'
        assert error.code == 'min_value'

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
        is_staff, 
        expected
    ):
        if is_staff is not None: authenticate(is_staff)
        product = baker.make(Product, slug=slug)
        collection = baker.make(Collection)
        payload = create_product_payload(collection_id=collection.id)
        url = get_products_detail_url(product.id)

        response = api_client.put(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data
