from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from autoslug import AutoSlugField
from phonenumber_field.modelfields import PhoneNumberField
from uuid import uuid4

class Cart(models.Model):
    """
    Temporary storage for Products before finalizing an Order.

    Does not require a Customer/User profile to create.
    """
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class CartItem(models.Model):
    """
    Products saved and added to a Cart.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_product_per_cart')
        ]


class Collection(models.Model):
    """
    Groups of Products with similar categories/uses.
    """
    title = models.CharField(max_length=255, unique=True)
    featured_product = models.ForeignKey('Product', on_delete=models.SET_NULL, related_name='+', blank=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    def clean(self):
        if(self.featured_product and self.featured_product.collection_id != self.pk):
            raise ValidationError({'featured_product': 'Featured product must be in this collection'})
        return super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['title']


class Customer(models.Model):
    """
    Profile for User using the online store.
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    phone_number = PhoneNumberField()
    birth_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    @admin.display(ordering='user__username')
    def username(self):
        return self.user.username

    @admin.display(ordering='user__first_name')
    def first_name(self):
        return self.user.first_name

    @admin.display(ordering='user__last_name')
    def last_name(self):
        return self.user.last_name
    
    def email(self):
        return self.user.email
    
    @admin.display(ordering='user__last_login')
    def last_login(self):
        return self.user.last_login


class Order(models.Model):
    """
    Finalized Cart that accepts or has accepted payment.

    Requires Customer/User profile to create.
    """
    STATUS_PENDING = 'P'
    STATUS_SHIPPED = 'S'
    STATUS_TRANSIT = 'T'
    STATUS_DELIVERY = 'D'
    STATUS_COMPLETE = 'C'
    STATUS_FAILED = 'F'
    STATUS_CANCELLED = 'X'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_TRANSIT, 'In Transit'),
        (STATUS_DELIVERY, 'Out for Delivery'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_CANCELLED, 'Cancelled')
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    placed_at = models.DateTimeField(auto_now_add=True)
    
    def cancel(self):
        if self.status != self.STATUS_PENDING:
            raise ValidationError({'status': 'Only pending orders can be cancelled.'})
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status'])

    @admin.display(ordering='customer__id')
    def customer_id(self):
        return self.customer.id
    
    class Meta:
        ordering = ['placed_at']


class OrderItem(models.Model):
    """
    Products saved and added to an Order.
    """
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='orderitems')
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['product__price', 'quantity']


class Product(models.Model):
    """
    Item that can be viewed and added to a Cart/Order.
    """
    title = models.CharField(max_length=255, unique=True)
    slug = AutoSlugField(populate_from='title')
    price = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(1)])
    description = models.CharField(max_length=255)
    inventory = models.IntegerField(validators=[MinValueValidator(0)])
    last_update = models.DateTimeField(auto_now=True)
    collection = models.ForeignKey(Collection, on_delete=models.PROTECT, related_name='products')

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['title']


class Review(models.Model):
    """
    Description from Customer/User about their experience/satisfaction with Product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)