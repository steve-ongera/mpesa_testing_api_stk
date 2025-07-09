from django.contrib import admin
from .models import Product, Order, MpesaTransaction

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)
    list_filter = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'product__name')
    readonly_fields = ('created_at',)

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('order', 'checkout_request_id', 'mpesa_receipt_number', 'amount', 'status', 'transaction_date')
    search_fields = ('checkout_request_id', 'mpesa_receipt_number')
    list_filter = ('status', 'transaction_date')
