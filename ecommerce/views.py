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
import logging
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@login_required
def checkout(request, product_id):
    """Checkout page for a product with debugging"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        quantity = int(request.POST.get('quantity', 1))
        total_amount = product.price * quantity
        
        # Debug: Print received data
        print(f"=== CHECKOUT DEBUG ===")
        print(f"Phone Number: {phone_number}")
        print(f"Quantity: {quantity}")
        print(f"Total Amount: {total_amount}")
        print(f"Product: {product.name}")
        print(f"User: {request.user.username}")
        
        # Validate phone number format
        if not phone_number:
            print("ERROR: Phone number is empty!")
            messages.error(request, 'Phone number is required.')
            return render(request, 'checkout.html', {'product': product})
        
        # Clean phone number (remove spaces, hyphens, etc.)
        phone_number = phone_number.replace(' ', '').replace('-', '').replace('+', '')
        
        # Validate Kenyan phone number format
        if not phone_number.startswith('254'):
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('7') or phone_number.startswith('1'):
                phone_number = '254' + phone_number
        
        print(f"Formatted Phone Number: {phone_number}")
        
        # Validate phone number length (should be 12 digits for Kenya: 254XXXXXXXXX)
        if len(phone_number) != 12:
            print(f"ERROR: Invalid phone number length: {len(phone_number)}")
            messages.error(request, 'Invalid phone number format. Use format: 254XXXXXXXXX')
            return render(request, 'checkout.html', {'product': product})
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            product=product,
            quantity=quantity,
            total_amount=total_amount,
            phone_number=phone_number
        )
        
        print(f"Order created: ID={order.id}")
        
        # Initiate M-Pesa payment
        mpesa_api = MpesaAPI()
        try:
            print("=== INITIATING STK PUSH ===")
            print(f"Phone: {phone_number}")
            print(f"Amount: {total_amount}")
            print(f"Order ID: {order.id}")
            
            response = mpesa_api.stk_push(phone_number, total_amount, order.id)
            
            print("=== M-PESA RESPONSE ===")
            print(f"Full Response: {json.dumps(response, indent=2)}")
            
            if response.get('ResponseCode') == '0':
                print("SUCCESS: STK Push initiated successfully!")
                
                # Create transaction record
                transaction = MpesaTransaction.objects.create(
                    order=order,
                    checkout_request_id=response['CheckoutRequestID'],
                    merchant_request_id=response['MerchantRequestID'],
                    phone_number=phone_number,
                    amount=total_amount
                )
                
                print(f"Transaction created: ID={transaction.id}")
                print(f"CheckoutRequestID: {response['CheckoutRequestID']}")
                print(f"MerchantRequestID: {response['MerchantRequestID']}")
                
                messages.success(request, 'Payment request sent! Check your phone.')
                return redirect('payment_status', order_id=order.id)
            else:
                print("ERROR: STK Push failed!")
                print(f"Response Code: {response.get('ResponseCode')}")
                print(f"Response Description: {response.get('ResponseDescription')}")
                print(f"Error Code: {response.get('errorCode')}")
                print(f"Error Message: {response.get('errorMessage')}")
                
                messages.error(request, f'Payment failed: {response.get("ResponseDescription", "Unknown error")}')
                order.status = 'failed'
                order.save()
        
        except Exception as e:
            print("=== EXCEPTION OCCURRED ===")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Message: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            
            messages.error(request, f'Payment error: {str(e)}')
            order.status = 'failed'
            order.save()
    
    return render(request, 'checkout.html', {'product': product})


import json
import datetime
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

@login_required
def payment_status(request, order_id):
    """Check payment status with automatic timeout detection"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    print(f"=== PAYMENT STATUS CHECK ===")
    print(f"Order ID: {order.id}")
    print(f"Order Status: {order.status}")
    print(f"Phone Number: {order.phone_number}")
    print(f"Total Amount: {order.total_amount}")
    
    # Check if order should be marked as failed due to timeout
    if order.status == 'pending':
        # Check if order is older than 1 minutes (STK push timeout)
        time_diff = timezone.now() - order.created_at
        if time_diff.total_seconds() > 60:  # 1 minutes in seconds
            print(f"Order timeout detected: {time_diff.total_seconds()} seconds")
            order.status = 'failed'
            order.save()
            
            # Also update transaction if it exists
            try:
                transaction = MpesaTransaction.objects.get(order=order)
                if transaction.status == 'pending':
                    transaction.status = 'failed'
                    transaction.save()
                    print("Transaction marked as failed due to timeout")
            except MpesaTransaction.DoesNotExist:
                pass
    
    # Check if transaction exists
    transaction = None
    try:
        transaction = MpesaTransaction.objects.get(order=order)
        print(f"Transaction Status: {transaction.status}")
        print(f"CheckoutRequestID: {transaction.checkout_request_id}")
        if transaction.mpesa_receipt_number:
            print(f"M-Pesa Receipt: {transaction.mpesa_receipt_number}")
    except MpesaTransaction.DoesNotExist:
        print("No transaction record found!")
    
    return render(request, 'payment_status.html', {
        'order': order,
        'transaction': transaction
    })

@csrf_exempt
def mpesa_callback(request):
    """Handle M-Pesa callback with detailed logging"""
    print("=== M-PESA CALLBACK RECEIVED ===")
    print(f"Method: {request.method}")
    print(f"Headers: {dict(request.headers)}")
    
    if request.method == 'POST':
        try:
            raw_body = request.body.decode('utf-8')
            print(f"Raw Callback Body: {raw_body}")
            
            callback_data = json.loads(raw_body)
            print(f"Parsed Callback Data: {json.dumps(callback_data, indent=2)}")
            
            # Extract callback data
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            result_desc = stk_callback.get('ResultDesc')
            
            print(f"Result Code: {result_code}")
            print(f"Result Description: {result_desc}")
            print(f"CheckoutRequestID: {checkout_request_id}")
            
            # Find transaction
            try:
                transaction = MpesaTransaction.objects.get(
                    checkout_request_id=checkout_request_id
                )
                print(f"Transaction found: {transaction.id}")
                
                if result_code == 0:  # Success
                    print("Payment successful!")
                    
                    # Extract payment details
                    callback_metadata = stk_callback.get('CallbackMetadata', {})
                    items = callback_metadata.get('Item', [])
                    
                    print(f"Callback Items: {json.dumps(items, indent=2)}")
                    
                    mpesa_receipt_number = None
                    transaction_date = None
                    
                    for item in items:
                        if item.get('Name') == 'MpesaReceiptNumber':
                            mpesa_receipt_number = item.get('Value')
                        elif item.get('Name') == 'TransactionDate':
                            transaction_date = item.get('Value')
                    
                    print(f"M-Pesa Receipt: {mpesa_receipt_number}")
                    print(f"Transaction Date: {transaction_date}")
                    
                    # Update transaction
                    transaction.status = 'completed'
                    transaction.mpesa_receipt_number = mpesa_receipt_number
                    if transaction_date:
                        transaction.transaction_date = datetime.datetime.strptime(
                            str(transaction_date), '%Y%m%d%H%M%S'
                        )
                    transaction.save()
                    
                    # Update order
                    transaction.order.status = 'paid'
                    transaction.order.save()
                    
                    print("Transaction and order updated successfully!")
                    
                else:  # Failed or Cancelled
                    print(f"Payment failed/cancelled with code: {result_code}")
                    print(f"Failure reason: {result_desc}")
                    
                    # Check if it's a user cancellation
                    if result_code == 1032:  # User cancelled
                        print("User cancelled the transaction")
                    elif result_code == 1037:  # User cannot be reached
                        print("User cannot be reached")
                    elif result_code == 1001:  # Insufficient funds
                        print("Insufficient funds")
                    elif result_code == 2001:  # Wrong PIN
                        print("Wrong PIN entered")
                    
                    transaction.status = 'failed'
                    transaction.save()
                    
                    transaction.order.status = 'failed'
                    transaction.order.save()
                    
            except MpesaTransaction.DoesNotExist:
                print(f"ERROR: Transaction not found for CheckoutRequestID: {checkout_request_id}")
                
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {str(e)}")
            print(f"Raw body: {request.body}")
        except Exception as e:
            print(f"Callback error: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
    
    return HttpResponse('OK')

# Add this new view for AJAX status checking
@login_required
def check_payment_status(request, order_id):
    """AJAX endpoint to check payment status"""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check for timeout
        if order.status == 'pending':
            time_diff = timezone.now() - order.created_at
            if time_diff.total_seconds() > 300:  # 5 minutes timeout
                order.status = 'failed'
                order.save()
                
                # Update transaction
                try:
                    transaction = MpesaTransaction.objects.get(order=order)
                    if transaction.status == 'pending':
                        transaction.status = 'failed'
                        transaction.save()
                except MpesaTransaction.DoesNotExist:
                    pass
        
        return JsonResponse({
            'status': order.status,
            'message': order.get_status_display(),
            'order_id': order.id
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)

# Additional debugging function to test M-Pesa API connection
def test_mpesa_connection():
    """Test M-Pesa API connection"""
    print("=== TESTING M-PESA API CONNECTION ===")
    
    try:
        mpesa_api = MpesaAPI()
        
        # Test authentication
        print("Testing authentication...")
        # You might need to add a method to test auth in your MpesaAPI class
        
        # Test with a sample request (use your test credentials)
        test_phone = "254708374149"  # Safaricom test number
        test_amount = 1
        test_order_id = 999999
        
        print(f"Testing STK Push to {test_phone} for amount {test_amount}")
        response = mpesa_api.stk_push(test_phone, test_amount, test_order_id)
        
        print(f"Test Response: {json.dumps(response, indent=2)}")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

# Add this to your MpesaAPI class for better debugging
class MpesaAPIDebug:
    def stk_push(self, phone_number, amount, order_id):
        """STK Push with debugging"""
        print(f"=== STK PUSH METHOD CALLED ===")
        print(f"Phone: {phone_number}")
        print(f"Amount: {amount}")
        print(f"Order ID: {order_id}")
        
        # Add your existing STK push logic here
        # Make sure to print the request payload before sending
        
        payload = {
            'BusinessShortCode': 'YOUR_SHORTCODE',
            'Password': 'YOUR_PASSWORD',
            'Timestamp': 'YOUR_TIMESTAMP',
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone_number,
            'PartyB': 'YOUR_SHORTCODE',
            'PhoneNumber': phone_number,
            'CallBackURL': 'YOUR_CALLBACK_URL',
            'AccountReference': f'Order{order_id}',
            'TransactionDesc': 'Payment for order'
        }
        
        print(f"Request Payload: {json.dumps(payload, indent=2)}")
        
        # Make the actual API call here
        # response = requests.post(url, json=payload, headers=headers)
        # print(f"API Response: {response.text}")
        
        return {}