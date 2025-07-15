from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import ProductFilter
from .models import Cart, CartItem, Collection, Customer, Order, OrderItem, Product, Review
from .pagination import DefaultPagination
from .permissions import IsAdminOrReadyOnly
from .serializers import (
    CartSerializer, CartItemSerializer, CartItemPostSerializer, CartItemPatchSerializer,
    CollectionSerializer, CustomerSerializer,
    OrderSerializer, OrderPostSerializer, OrderPatchSerializer,
    OrderItemSerializer,
    ProductSerializer, ReviewSerializer
)

class CartViewSet(ModelViewSet):
    queryset = Cart.objects.prefetch_related('items__product').all()
    serializer_class = CartSerializer


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product__title']
    ordering_fields = ['product__price', 'quantity']

    def get_queryset(self):
        return CartItem.objects \
            .filter(cart_id=self.kwargs['cart_pk']) \
            .select_related('product')

    def get_serializer_class(self):
        match self.action:
            case 'create': return CartItemPostSerializer
            case 'partial_update': return CartItemPatchSerializer
            case _: return CartItemSerializer

    def get_serializer_context(self):
        return {'cart_id': self.kwargs['cart_pk']}


class CollectionViewSet(ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count('products')).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadyOnly]

    def destroy(self, request, *args, **kwargs):
        if Product.objects.filter(collection_id=kwargs['pk']).exists():
            return Response(
                'Collection cannot be deleted because it includes one or more products.',
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        return super().destroy(request, *args, **kwargs)


class CustomerViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'delete']

    queryset = Customer.objects.select_related('user').all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def create(self, request, *args, **kwargs):
        serializer = OrderPostSerializer(
            data=request.data,
            context={'user_id': self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        serializer = OrderSerializer(order)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        user = self.request.user
        orders = Order.objects.prefetch_related('items__product')
        return orders if user.is_staff else orders.filter(customer__user=user)

    def get_serializer_class(self):
        match self.action:
            case 'create': return OrderPostSerializer
            case 'partial_update': return OrderPatchSerializer
            case _: return OrderSerializer

    def get_permissions(self):
        if self.action == 'destroy' or self.action == 'partial_update':
            return [IsAdminUser()]
        return [IsAuthenticated()]


class OrderItemViewSet(ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product__title']
    ordering_fields = ['product__price', 'quantity']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects \
            .filter(order_id=self.kwargs['order_pk']) \
            .select_related('product')


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.annotate(review_count=Count('reviews')).order_by('title').all()
    serializer_class = ProductSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = ProductFilter
    ordering_fields = ['title', 'price', 'last_update']
    pagination_class = DefaultPagination
    permission_classes = [IsAdminOrReadyOnly]
    search_fields = ['title']
    

class ReviewViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk'])
    
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk']}