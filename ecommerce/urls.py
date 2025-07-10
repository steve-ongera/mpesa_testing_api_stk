from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('checkout/<int:product_id>/', views.checkout, name='checkout'),
    path('payment-status/<int:order_id>/', views.payment_status, name='payment_status'),
    path('check-payment-status/<int:order_id>/', views.check_payment_status, name='check_payment_status'),  # New AJAX endpoint
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
     path('logout/', views.logout_view, name='logout'),
]
