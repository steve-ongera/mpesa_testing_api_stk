from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('payment-status/<int:order_id>/', views.payment_status, name='payment_status'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]
