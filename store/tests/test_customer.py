import pytest
from model_bakery import baker
from rest_framework import status
from store.models import Customer

# Fields displayed to User when a Customer is returned.
serializer_fields = [
    'id',
    'username',
    'email',
    'phone_number',
    'birth_date'
]

# model_bakery baker does not support PhoneNumberField.
# A generic number is given to bypass TypeError.
phone_number = '+18005551234'

def get_customers_detail_url(id):
    from django.urls import reverse
    return reverse('customers-detail', kwargs={'pk': id})

def get_customers_list_url():
    from django.urls import reverse
    return reverse('customers-list')

def create_customer_payload(**overrides):
    payload = {
        'username': 'U',
        'first_name': 'F',
        'last_name': 'L',
        'email': 'test@email.com',
        'password': '1a2s3d4f5gqwertymp',
        'confirm_password': '1a2s3d4f5gqwertymp',
        'phone_number': phone_number
    }
    payload.update(overrides)
    return payload

# Tests.

@pytest.mark.django_db
class TestCreateCustomer:

    # Validation.
    MISSING_FIELD_PAYLOADS = [
        ('username', 
         {'first_name': 'F', 'last_name': 'L', 'email': 'test@email.com',
          'password': '1a2s3d4f5gqwertymp', 'confirm_password': '1a2s3d4f5gqwertymp',
          'phone_number': phone_number}),
        ('first_name',
         {'username': 'U', 'last_name': 'L', 'email': 'test@email.com',
          'password': '1a2s3d4f5gqwertymp', 'confirm_password': '1a2s3d4f5gqwertymp',
          'phone_number': phone_number}),
        ('last_name',
         {'username': 'U', 'first_name': 'F', 'email': 'test@email.com',
          'password': '1a2s3d4f5gqwertymp', 'confirm_password': '1a2s3d4f5gqwertymp',
          'phone_number': phone_number}),
        ('email',
         {'username': 'U', 'first_name': 'F', 'last_name': 'L',
          'password': '1a2s3d4f5gqwertymp', 'confirm_password': '1a2s3d4f5gqwertymp',
          'phone_number': phone_number}),
        ('password',
         {'username': 'U', 'first_name': 'F', 'last_name': 'L', 'email': 'test@email.com',
          'confirm_password': '1a2s3d4f5gqwertymp',
          'phone_number': phone_number}),
        ('confirm_password',
         {'username': 'U', 'first_name': 'F', 'last_name': 'L', 'email': 'test@email.com',
          'password': '1a2s3d4f5gqwertymp',
          'phone_number': phone_number}),
        ('phone_number',
         {'username': 'U', 'first_name': 'F', 'last_name': 'L', 'email': 'test@email.com',
          'password': '1a2s3d4f5gqwertymp', 'confirm_password': '1a2s3d4f5gqwertymp'}),
          
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
        url = get_customers_list_url()

        response = api_client.post(url, payload)
        data = response.data
        error = data[missing_field][0]
        
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
        payload = create_customer_payload()
        url = get_customers_list_url()

        response = api_client.post(url, payload)
        data = response.data

        assert response.status_code == expected
        if is_staff:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestDestoryCustomer:
    # TODO: Customers can delete their own profile?

    # Validation.
    def test_if_customer_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True)
        url = get_customers_detail_url(-1) # -1 used as garbage value.

        response = api_client.delete(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Customer matches the given query.'
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
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            customer = baker.make(Customer, user=user, phone_number=phone_number)
        else: customer = baker.make(Customer, phone_number=phone_number)
        url = get_customers_detail_url(customer.id)

        response = api_client.delete(url)

        assert response.status_code == expected


@pytest.mark.django_db
class TestListCustomer:

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
        url = get_customers_list_url()

        response = api_client.get(url)
        print(response.data)

        assert response.status_code == expected


@pytest.mark.django_db
class TestPartialUpdateCustomer:
    # TODO: Customer should be able to update their profile

    # Validation.
    # Currently returns 200; model/serializer needs to be adjusted
    def test_if_birth_date_is_in_future_return_400(self, authenticate, partial_update_customer):
        from datetime import date, timedelta
        authenticate(True)
        customer = baker.make(Customer, phone_number=phone_number)
        birth_date = date.today() + timedelta(days=1)
        password = customer.user.password
        payload = {'birth_date': birth_date,'password': password, 'confirm_password': password}

        response = partial_update_customer(customer, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

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
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            customer = baker.make(Customer, user=user, phone_number=phone_number)
        else: customer = baker.make(Customer, phone_number=phone_number)
        new_username = 'new_username'
        password = customer.user.password
        payload = {'username': new_username, 'password': password, 'confirm_password': password}
        url = get_customers_detail_url(customer.id)

        response = api_client.patch(url, payload)
        data = response.data
        
        assert response.status_code == expected
        if is_staff: # TODO: is not None:
            for field in serializer_fields: assert field in data
            assert data['username'] == new_username


@pytest.mark.django_db
class TestRetrieveCustomer:
    # TODO: Only admin can retrieve. Auth user should be able to grab their profile

    # Validation.
    def test_if_customer_does_not_exist_returns_404(self, api_client, authenticate):
        authenticate(True) 
        url = get_customers_detail_url(-1) # -1 used as garbage value.

        response = api_client.get(url)
        data = response.data
        error = data['detail']

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error == 'No Customer matches the given query.'
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
        is_staff,
        expected
    ):
        if is_staff is not None:
            user = authenticate(is_staff)
            customer = baker.make(Customer, user=user, phone_number=phone_number)
        else: customer = baker.make(Customer, phone_number=phone_number)
        url = get_customers_detail_url(customer.id)

        response = api_client.get(url)
        data = response.data
        
        assert response.status_code == expected
        if is_staff: # TODO: is not None:
            for field in serializer_fields: assert field in data


@pytest.mark.django_db
class TestUpdateCustomer:
    # TODO: Remove Update from CustomerViewSet
    pass
