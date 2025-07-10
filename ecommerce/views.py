from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Order, MpesaTransaction
from .mpesa_utils import MpesaAPI
import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate , logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('product_list')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('product_list')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        # Basic validation
        if not username or not password or not password2:
            messages.error(request, "All fields are required.")
        elif password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('products')
    
    return render(request, 'auth/signup.html')

def product_list(request):
    """Display all products"""
    products = Product.objects.all()
    return render(request, 'products.html', {'products': products})

@login_required
def checkout(request, product_id):
    """Checkout page for a product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        quantity = int(request.POST.get('quantity', 1))
        total_amount = product.price * quantity
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            product=product,
            quantity=quantity,
            total_amount=total_amount,
            phone_number=phone_number
        )
        
        # Initiate M-Pesa payment
        mpesa_api = MpesaAPI()
        try:
            response = mpesa_api.stk_push(phone_number, total_amount, order.id)
            
            if response.get('ResponseCode') == '0':
                # Create transaction record
                MpesaTransaction.objects.create(
                    order=order,
                    checkout_request_id=response['CheckoutRequestID'],
                    merchant_request_id=response['MerchantRequestID'],
                    phone_number=phone_number,
                    amount=total_amount
                )
                
                messages.success(request, 'Payment request sent! Check your phone.')
                return redirect('payment_status', order_id=order.id)
            else:
                messages.error(request, 'Payment failed. Please try again.')
                order.status = 'failed'
                order.save()
        
        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
            order.status = 'failed'
            order.save()
    
    return render(request, 'checkout.html', {'product': product})

def payment_status(request, order_id):
    """Check payment status"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payment_status.html', {'order': order})

import datetime
@csrf_exempt
def mpesa_callback(request):
    """Handle M-Pesa callback"""
    if request.method == 'POST':
        try:
            callback_data = json.loads(request.body)
            
            # Extract callback data
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            
            # Find transaction
            try:
                transaction = MpesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
                
                if result_code == 0:  # Success
                    # Extract payment details
                    callback_metadata = stk_callback.get('CallbackMetadata', {})
                    items = callback_metadata.get('Item', [])
                    
                    mpesa_receipt_number = None
                    transaction_date = None
                    
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            mpesa_receipt_number = item.get('Value')
                        elif item.get('Name') == 'TransactionDate':
                            transaction_date = item.get('Value')
                    
                    # Update transaction
                    transaction.status = 'completed'
                    transaction.mpesa_receipt_number = mpesa_receipt_number
                    if transaction_date:
                        transaction.transaction_date = datetime.strptime(
                            str(transaction_date), '%Y%m%d%H%M%S'
                        )
                    transaction.save()
                    
                    # Update order
                    transaction.order.status = 'paid'
                    transaction.order.save()
                    
                else:  # Failed
                    transaction.status = 'failed'
                    transaction.save()
                    
                    transaction.order.status = 'failed'
                    transaction.order.save()
                    
            except MpesaTransaction.DoesNotExist:
                pass  # Transaction not found
                
        except Exception as e:
            print(f"Callback error: {str(e)}")
    
    return HttpResponse('OK')