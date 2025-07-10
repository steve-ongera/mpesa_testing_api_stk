# M-Pesa E-commerce API Testing Application

A Django-based e-commerce application integrated with M-Pesa STK Push for mobile payments testing in Kenya.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## 🌟 Overview

This application provides a complete e-commerce solution with M-Pesa payment integration for testing purposes. It includes user authentication, product management, order processing, and real-time payment status tracking using M-Pesa's STK Push API.

## ✨ Features

### Core Features
- **User Authentication**: Registration, login, and logout functionality
- **Product Management**: Display and browse products
- **Shopping Cart**: Add products and manage quantities
- **M-Pesa Integration**: STK Push payment processing
- **Order Management**: Track order status and payment history
- **Real-time Status Updates**: AJAX-based payment status checking

### M-Pesa Features
- STK Push payment initiation
- Callback handling for payment notifications
- Transaction status tracking
- Automatic timeout detection (1 minute for testing)
- Detailed logging for debugging

### Security Features
- CSRF protection
- User authentication required for checkout
- Phone number validation (Kenyan format)
- Secure callback handling

## 🔧 Prerequisites

- Python 3.8+
- Django 3.2+
- M-Pesa Developer Account (Safaricom)
- MySQL/PostgreSQL (optional, SQLite for development)

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mpesa-ecommerce-testing
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## ⚙️ Configuration

### M-Pesa API Configuration

1. **Register on Safaricom Developer Portal**
   - Visit: https://developer.safaricom.co.ke/
   - Create an account and get your credentials

2. **Configure M-Pesa Settings**
   Create a `mpesa_config.py` file in your project root:
   ```python
   # M-Pesa API Configuration
   MPESA_CONSUMER_KEY = 'your_consumer_key'
   MPESA_CONSUMER_SECRET = 'your_consumer_secret'
   MPESA_BUSINESS_SHORT_CODE = 'your_business_short_code'
   MPESA_PASSKEY = 'your_passkey'
   MPESA_CALLBACK_URL = 'https://yourdomain.com/mpesa/callback/'
   
   # For testing, use sandbox URLs
   MPESA_ENVIRONMENT = 'sandbox'  # or 'production'
   ```

3. **Update Django Settings**
   Add to your `settings.py`:
   ```python
   from .mpesa_config import *
   
   # Add your domain for callback URL
   ALLOWED_HOSTS = ['yourdomain.com', 'localhost', '127.0.0.1']
   ```

### Database Configuration

For production, configure your database in `settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🚀 Usage

### For Users

1. **Registration/Login**
   - Navigate to `/signup/` to create an account
   - Use `/login/` to access existing account

2. **Shopping**
   - Browse products on the home page
   - Click on products to view details
   - Proceed to checkout

3. **Payment Process**
   - Enter your M-Pesa phone number (254XXXXXXXXX format)
   - Select quantity
   - Click "Pay with M-Pesa"
   - Check your phone for STK Push prompt
   - Enter your M-Pesa PIN
   - Wait for payment confirmation

### For Developers

1. **Testing M-Pesa Integration**
   ```python
   # Use the test function in views.py
   test_mpesa_connection()
   ```

2. **Monitoring Payments**
   - Check Django logs for detailed payment flow
   - Monitor the `/payment_status/<order_id>/` endpoint
   - Use browser developer tools to see AJAX requests

## 🔗 API Endpoints

### Authentication
- `POST /login/` - User login
- `POST /signup/` - User registration  
- `GET /logout/` - User logout

### Products & Orders
- `GET /` - Product listing
- `GET /checkout/<product_id>/` - Checkout page
- `POST /checkout/<product_id>/` - Process checkout

### Payment
- `GET /payment_status/<order_id>/` - Payment status page
- `GET /api/payment_status/<order_id>/` - AJAX payment status
- `POST /mpesa/callback/` - M-Pesa callback handler

## 🧪 Testing

### Unit Tests
```bash
python manage.py test
```

### Manual Testing

1. **Test with Safaricom Test Numbers**
   - Use `254708374149` for testing
   - Use small amounts (1 KES) for testing

2. **Test Scenarios**
   - Successful payment
   - User cancellation
   - Timeout scenarios
   - Invalid phone numbers
   - Network failures

### Debugging

Enable detailed logging:
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'mpesa_debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 🐛 Troubleshooting

### Common Issues

1. **STK Push Not Received**
   - Check phone number format (254XXXXXXXXX)
   - Verify M-Pesa credentials
   - Ensure callback URL is accessible

2. **Callback Not Working**
   - Check callback URL is publicly accessible
   - Verify CSRF exemption on callback view
   - Check server logs for callback data

3. **Payment Status Not Updating**
   - Check callback URL configuration
   - Verify transaction records in database
   - Check for network connectivity issues

### Debug Mode

The application includes extensive logging. Check console output for:
- Payment initiation details
- M-Pesa API responses
- Callback data
- Transaction status updates

## 📱 Phone Number Formats

The application accepts various phone number formats and automatically converts them:
- `0712345678` → `254712345678`
- `712345678` → `254712345678`
- `+254712345678` → `254712345678`
- `254712345678` → `254712345678` (no change)

## 🔒 Security Considerations

- Always use HTTPS in production
- Secure your M-Pesa credentials
- Implement rate limiting for payment requests
- Validate all callback data
- Use environment variables for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Contact

**Steve Ongera**  
**Kencom Softwares Ltd**

- **Email**: steveongera001@gmail.com
- **Phone**: +254 112 284 093
- **Company**: Kencom Softwares Ltd

---

## 🔧 Technical Support

For technical support and custom development:
- Email: steveongera001@gmail.com
- Phone: +254 112 284 093

## 🌐 About Kencom Softwares Ltd

Kencom Softwares Ltd specializes in:
- Custom software development
- Mobile payment integrations
- E-commerce solutions
- API integrations
- Django web applications

---

*This application is designed for testing M-Pesa integrations in a safe development environment. Always test thoroughly before deploying to production.*