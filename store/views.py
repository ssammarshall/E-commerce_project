from django.db.models.aggregates import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
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
    OrderItemSerializer, OrderItemPostSerializer, OrderItemPatchSerializer,
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

    serializer_class = CustomerSerializer

    def get_queryset(self):
        user = self.request.user
        customers = Customer.objects.select_related('user')
        return customers if user.is_staff else customers.filter(user=user)
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()] # 
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        '''
        Only admin users can view list of customers.
        '''
        user = self.request.user

        if user.is_staff:
            return super().list(request, *args, **kwargs)
        
        return Response(
            'Customer list only available to admin users',
            status=status.HTTP_403_FORBIDDEN
        )


class OrderViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    filter_backends = [OrderingFilter]
    ordering_fields = ['placed_at']
    pagination_class = DefaultPagination

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
        if self.action == 'partial_update':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @action(detail=True, methods=['get', 'post'], url_path='cancel') # 'get' method temporary for DRF Browsable API; requires front end interface.
    def cancel(self, request, pk=None):
        order: Order = self.get_object()

        if order.status != Order.STATUS_PENDING:
            return Response(
                'Only pending orders can be cancelled.',
                status=status.HTTP_400_BAD_REQUEST
            )

        order.cancel()
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrderItemViewSet(ModelViewSet):
    http_method_names = ['get', 'delete', 'post', 'patch', 'head', 'options']

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = ['product__price', 'quantity']
    pagination_class = DefaultPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects \
            .filter(order_id=self.kwargs['order_pk']) \
            .select_related('product')
    
    def get_serializer_class(self):
        match self.action:
            case 'create': return OrderItemPostSerializer
            case 'partial_update': return OrderItemPatchSerializer
            case _: return OrderItemSerializer
    
    def get_serializer_context(self):
        return {'order_id': self.kwargs['order_pk']}


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

    filter_backends = [OrderingFilter]
    ordering_fields = ['date']
    pagination_class = DefaultPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs['product_pk']).order_by('date')
    
    def get_serializer_context(self):
        return {'product_id': self.kwargs['product_pk'], 'request': self.request}