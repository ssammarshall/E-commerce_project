import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Collection, Product

# Fields displayed to User when a Collection is returned.
serializer_fields = [
    'id',
    'title'
]

# model_bakery baker does not support AutoSlugField.
# # A generic slug is given to bypass TypeError.
slug = 'product-slug'

def get_collections_detail_url(id):
    from django.urls import reverse
    return reverse('collections-detail', kwargs={'pk': id})

def get_collections_list_url():
    from django.urls import reverse
    return reverse('collections-list')


# Tests.

@pytest.mark.django_db
class TestCreateCollection:

    # Validation.
    def test_if_missing_title_returns_400(self, api_client, authenticate):
        authenticate(True)
        url = get_collections_list_url()

        response = api_client.post(url, {})
        data = response.data
        error = data['title'][0]

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error == 'This field is required.'
        assert error.code == 'required'
    
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
        payload = {'title': 'a'}
        url = get_collections_list_url()

        response = api_client.post(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestDestoryCollection:

    # Validation.
    def test_if_collection_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_collections_detail_url(-1) # -1 used as garbage value.

        response = api_client.delete(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Collection matches the given query.'
        assert error.code == 'not_found'

    def test_if_collection_has_product_returns_405(self, api_client, authenticate):
        authenticate(True)
        collection = baker.make(Collection)
        baker.make(Product, collection=collection, slug=slug)
        url = get_collections_detail_url(collection.id)

        response = api_client.delete(url)
        data = response.data

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert data == 'Collection cannot be deleted because it includes one or more products.'

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
        collection = baker.make(Collection)
        url = get_collections_detail_url(collection.id)

        response = api_client.delete(url)

        assert response.status_code == expected


@pytest.mark.django_db
class TestListCollection:
    # TODO: pagination, search

    # Permissions.
    # Collections can be viewed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        num_of_collections = 5
        baker.make(Collection, _quantity=num_of_collections)
        url = get_collections_list_url()

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == status.HTTP_200_OK
        assert len(data) == num_of_collections
    

@pytest.mark.django_db
class TestPartialUpdateCollection:

    # Validation.
    def test_if_collection_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_collections_detail_url(-1) # -1 used as garbage value.

        response = api_client.patch(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Collection matches the given query.'
        assert error.code == 'not_found'


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
        collection = baker.make(Collection)
        new_title = 'new title'
        payload = {'title': new_title}
        url = get_collections_detail_url(collection.id)

        response = api_client.patch(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data
            assert data['title'] == new_title


@pytest.mark.django_db
class TestRetrieveCollection:

    # Validation.
    def test_if_collection_does_not_exist_returns_404(self, api_client):
        url = get_collections_detail_url(-1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Collection matches the given query.'
        assert error.code == 'not_found'

    # Permissions.
    # Collections can be viewed with or without authentication (Customer/User profile).
    IS_STAFF = [None, False, True]
    @pytest.mark.parametrize('is_staff', IS_STAFF)
    def test_user_permission_classes(
        self,
        api_client,
        authenticate,
        is_staff,
    ):
        if is_staff is not None: authenticate(is_staff)
        collection = baker.make(Collection)
        product_count = 5
        baker.make(Product, collection=collection, slug=slug, _quantity=product_count)
        url = get_collections_detail_url(collection.id)

        response = api_client.get(url)
        data = response.data

        assert response.status_code == status.HTTP_200_OK
        for field in serializer_fields: assert field in data
        assert data['products_count'] == product_count


@pytest.mark.django_db
class TestUpdateCollection:

    # Validation.
    def test_if_collection_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_collections_detail_url(-1) # -1 used as garbage value.

        response = api_client.put(url, {})
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Collection matches the given query.'
        assert error.code == 'not_found'


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
        collection = baker.make(Collection)
        new_title = 'new title'
        payload = {'title': new_title}
        url = get_collections_detail_url(collection.id)

        response = api_client.put(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data
            assert data['title'] == new_title
