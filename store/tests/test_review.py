import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Product, Review

# Fields displayed to User when a Review is returned.
serializer_fields = [
    'id',
    'name',
    'description',
    'date'
]

# model_bakery baker does not support AutoSlugField.
# # A generic slug is given to bypass TypeError.
slug = 'product-slug'

def get_reviews_detail_url(product_id, review_id):
    from django.urls import reverse
    return reverse('product-reviews-detail', kwargs={'product_pk': product_id, 'pk': review_id})

def get_reviews_list_url(product_id):
    from django.urls import reverse
    return reverse('product-reviews-list', kwargs={'product_pk': product_id})

def create_review_payload(product_id, **overrides):
    payload = {
        'product': product_id,
        'description': 'D'
    }
    payload.update(overrides)
    return payload

# Fixtures.

@pytest.fixture
# Return tuple of Product and Review.
def product_and_review():
    product = baker.make(Product, slug=slug)
    return (product, baker.make(Review, product=product))

# Tests.

@pytest.mark.django_db
class TestCreateReview:

    # Validation.
    def test_if_missing_description_returns_400(self, api_client, authenticate):
        authenticate(True)
        product = baker.make(Product, slug=slug)
        url = get_reviews_list_url(product_id=product.id)

        response = api_client.post(url, {})
        data = response.data
        error = data['description'][0]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'This field is required.'
        assert error.code == 'required'

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
        if is_staff is not None: authenticate(is_staff)
        product = baker.make(Product, slug=slug)
        payload = create_review_payload(product_id=product.id)
        url = get_reviews_list_url(product.id)

        response = api_client.post(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff is not None:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestDeleteReview:

    # Validation.
    def test_if_review_does_not_exist_returns_404(self, api_client, authenticate, product_and_review):
        authenticate(True)
        (product, review) = product_and_review
        url = get_reviews_detail_url(product.id, -1)

        response = api_client.delete(url)
        data = response.data
        error = data['detail']
 
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Review matches the given query.'
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
        product_and_review,
        is_staff,
        expected
    ):
        if is_staff is not None: authenticate(is_staff)
        (product, review) = product_and_review
        url = get_reviews_detail_url(product.id, review.id)

        response = api_client.delete(url)

        assert response.status_code == expected


@pytest.mark.django_db
class TestListReview:
    
    # Filter Backends.
    def test_if_list_can_order_by_date(self, api_client):
        product = baker.make(Product, slug=slug)
        baker.make(Review, product=product)

        # Ascending order.
        url = get_reviews_list_url(product.id) + '?ordering=date'

        response = api_client.get(url)
        data = response.data
        dates_ascending = [review['date'] for review in data.get('results', data)]

        assert response.status_code == status.HTTP_200_OK
        assert dates_ascending == sorted(dates_ascending)

        # Descending order.
        url = get_reviews_list_url(product.id) + '?ordering=-date'

        response = api_client.get(url)
        data = response.data
        dates_descending = [review['date'] for review in data.get('results', data)]

        assert response.status_code == status.HTTP_200_OK
        assert dates_descending == sorted(dates_descending, reverse=True)

    def test_if_list_has_pagination_present(self, api_client):
        from store.pagination import DefaultPagination
        max_num_of_pages = DefaultPagination.page_size
        product = baker.make(Product, slug=slug)
        baker.make(Review, product=product, _quantity=max_num_of_pages+1)
        url = get_reviews_list_url(product.id)

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert data['next'] != None
        assert data['previous'] == None
        assert data['results']
        assert len(data['results']) == max_num_of_pages


    # Permissions.
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        product_and_review,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        (product, review) = product_and_review
        url = get_reviews_list_url(product.id)

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert data['results'][0]['id'] == review.id


@pytest.mark.django_db
class TestPartialUpdateReview:

    # Validation.
    def test_if_review_does_not_exist_returns_404(self, api_client, authenticate, product_and_review):
        authenticate(True)
        (product, review) = product_and_review
        url = get_reviews_detail_url(product.id, -1) # -1 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Review matches the given query.'
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
        product_and_review,
        is_staff,
        expected
    ):
        if is_staff is not None: authenticate(is_staff)
        (product, review) = product_and_review
        new_description = 'new description'
        payload = {'description': new_description}
        url = get_reviews_detail_url(product.id, review.id)

        response = api_client.patch(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            assert data['id'] == review.id
            assert data['name'] == review.name
            assert data['description'] == new_description


@pytest.mark.django_db
class TestRetrieveReview:

    # Validation.
    def test_if_review_does_not_exist_returns_404(self, api_client, authenticate, product_and_review):
        authenticate(True)
        (product, review) = product_and_review
        url = get_reviews_detail_url(product.id, -1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Review matches the given query.'
        assert error.code == 'not_found'
    
    # Permissions.
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        product_and_review,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        (product, review) = product_and_review
        url = get_reviews_detail_url(product.id, review.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestUpdateReview:

    # Validation.
    def test_if_review_does_not_exist_returns_404(self, api_client, authenticate, product_and_review):
        authenticate(True)
        (product, review) = product_and_review
        url = get_reviews_detail_url(product.id, -1) # -1 used as garbage value.

        response = api_client.put(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Review matches the given query.'
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
        product_and_review,
        is_staff, 
        expected
    ):
        if is_staff is not None: authenticate(is_staff)
        (product, review) = product_and_review
        payload = create_review_payload(product_id=product.id)
        url = get_reviews_detail_url(product.id, review.id)

        response = api_client.put(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data
            