from rest_framework_nested import routers
from . import views

router = routers.DefaultRouter()

router.register('carts', views.CartViewSet)
carts_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
carts_router.register('items', views.CartItemViewSet, basename='cart-items')

router.register('collections', views.CollectionViewSet, basename='collections')

router.register('customers', views.CustomerViewSet, basename='customers')

router.register('orders', views.OrderViewSet, basename='orders')
orders_router = routers.NestedDefaultRouter(router, 'orders', lookup='order')
orders_router.register('items', views.OrderItemViewSet, basename='order-items')

router.register('products', views.ProductViewSet, basename='products')
products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('reviews', views.ReviewViewSet, basename='product-reviews')

urlpatterns = router.urls + carts_router.urls + orders_router.urls + products_router.urls