from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from decimal import Decimal
from .models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, Review

class ProductSerializer(serializers.ModelSerializer):
    review_count = serializers.IntegerField(read_only=True) # Number of reviews.

    class Meta:
        model = Product
        fields = ['id', 'title', 'price', 'description', 'inventory', 'collection', 'review_count']


class ProductSimpleSerializer(serializers.ModelSerializer):
    """
    ProductSerializer with less fields for easier readability.
    """
    class Meta:
        model = Product
        fields = ['id', 'title', 'price']


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSimpleSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item:CartItem):
        return Decimal(cart_item.quantity) * cart_item.product.price

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'total_price']


class CartItemPatchSerializer(serializers.ModelSerializer):
    """
    CartItemSerializer for updating quantity of existing CartItem.
    """
    class Meta:
        model = CartItem
        fields = ['quantity']


class CartItemPostSerializer(serializers.ModelSerializer):
    """
    CartItemSerializer for creating new CartItem.
    """
    product_id = serializers.IntegerField()

    @transaction.atomic
    def save(self, **kwargs):
        """
        Checks if a CartItem with the same product_id already exists and
        updates the CartItem's quantity.

        Otherwise creates a new CartItem.
        """
        cart_id = self.context['cart_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try: # If CartItem already exists in Cart.
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist: # If CartItem is not already in Cart.
            self.instance = CartItem.objects.create(cart_id=cart_id, **self.validated_data)

        return self.instance

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No product with given product id was found.')
        return value

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart:Cart):
        return sum([item.quantity * item.product.price for item in cart.items.all()])

    class Meta:
        model = Cart
        fields = ['id', 'created_at', 'items', 'total_price']


class CollectionSerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collection
        fields = ['id', 'title', 'products_count']


class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=150,
        validators=[UniqueValidator(get_user_model().objects.all(), message='Username is already in use.')]
    )
    first_name = serializers.CharField(max_length=150, write_only=True)
    last_name = serializers.CharField(max_length=150, write_only=True)
    email = serializers.EmailField(
        validators=[UniqueValidator(get_user_model().objects.all(), message='Email already in use.')]
    )
    password = serializers.CharField(style={"input_type": "password"}, write_only=True)
    confirm_password = serializers.CharField(style={"input_type": "password"}, write_only=True)

    @transaction.atomic
    def create(self, validated_data):
        """
        Creates a new Customer together with its auth User in one call.
        """
        username = validated_data.pop('username')
        first = validated_data.pop('first_name')
        last = validated_data.pop('last_name')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        validated_data.pop('confirm_password')

        User = get_user_model()
        user = User.objects.create_user(
            username=username,
            first_name=first,
            last_name=last,
            email=email,
            password=password
        )
        user.save()

        return Customer.objects.create(user=user, **validated_data)
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match'})
        validate_password(attrs['password'])
        return super().validate(attrs)

    class Meta:
        model = Customer
        fields = [
            'id',
            'username', 'first_name', 'last_name', 'email', # User fields.
            'password', 'confirm_password', # Django password validation fields.
            'phone_number', 'birth_date' # Customer fields.
        ]


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSimpleSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, order_item:OrderItem):
        return Decimal(order_item.quantity) * order_item.product.price

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'total_price']


class OrderItemPatchSerializer(serializers.ModelSerializer):
    """
    OrderItemSerializer for updating quantity of existing OrderItem.
    """
    class Meta:
        model = CartItem
        fields = ['quantity']


class OrderItemPostSerializer(serializers.ModelSerializer):
    """
    OrderItemSerializer for creating new OrderItem.
    """
    product_id = serializers.IntegerField()

    @transaction.atomic
    def save(self, **kwargs):
        """
        Checks if a OrderItem with the same product_id already exists and
        updates the OrderItem's quantity.

        Otherwise creates a new OrderItem.
        """
        order_id = self.context['order_id']
        product_id = self.validated_data['product_id']
        quantity = self.validated_data['quantity']

        try: # If OrderItem already exists in Order.
            order_id = OrderItem.objects.get(order_id=order_id, product_id=product_id)
            order_id.quantity += quantity
            order_id.save()
            self.instance = order_id
        except OrderItem.DoesNotExist: # If OrderItem is not already in Order.
            self.instance = OrderItem.objects.create(order_id=order_id, **self.validated_data)

        return self.instance

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError('No product with given product id was found.')
        return value

    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, order:Order):
        return sum([item.quantity * item.product.price for item in order.items.all()])
    
    class Meta:
        model = Order
        fields = ['id', 'payment_status', 'placed_at', 'items', 'total_price']


class OrderPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['payment_status']


class OrderPostSerializer(serializers.ModelSerializer):
    cart_id = serializers.UUIDField(write_only=True)

    @transaction.atomic
    def create(self, validated_data):
        """
        Create new Order using a pre-existing Cart.

        OrderItems are created from the Cart's CartItems then the Cart is deleted.
        """
        try:
            customer = Customer.objects.get(user_id=self.context['user_id'])
            order = Order.objects.create(customer=customer)
            cart_id = validated_data['cart_id']
            cart_items = CartItem.objects.select_related('product').filter(cart_id=cart_id)

            if not cart_items:
                raise serializers.ValidationError('No items found in cart. Cannot create an empty order.')

            OrderItem.objects.bulk_create(
                OrderItem(order=order, product=item.product, quantity=item.quantity)
                for item in cart_items
            )

            Cart.objects.filter(pk=cart_id).delete()
        except Customer.DoesNotExist:
            raise serializers.ValidationError('No customer with given user id was found.')
        except Cart.DoesNotExist:
            raise serializers.ValidationError('No cart with given cart id was found.')
        
        return order
    
    class Meta:
        model = Order
        fields = ['cart_id']


class ReviewSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)

    def create(self, validated_data):
        product_id = self.context['product_id']
        request = self.context['request']
        user = request.user
        username=user.username
        return Review.objects.create(product_id=product_id, name=username, **validated_data)

    class Meta:
        model = Review
        fields = ['id', 'name', 'description', 'date']
