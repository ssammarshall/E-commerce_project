from django.contrib import admin
from .models import *

class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'customer'
    fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': ['phone_number', 'birth_date'],
        })
    ]


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['featured_product']
    list_display = ['title']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'last_login']
    list_select_related = ['user']
    ordering = ['user__username', 'user__first_name', 'user__last_name', 'user__last_login']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'status', 'placed_at']
    list_filter = ['status', 'placed_at']
    list_per_page = 10
    list_select_related = ['customer']
    ordering = ['placed_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'price', 'inventory', 'collection_title']
    list_editable = ['price']
    list_filter = ['collection', 'last_update']
    list_per_page = 10
    list_select_related = ['collection']
    ordering = ['title', 'price']
    search_fields = ['title']

    def collection_title(self, product:Product):
        return product.collection.title