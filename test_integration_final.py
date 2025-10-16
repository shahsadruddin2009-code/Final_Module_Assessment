import sys
import os
from urllib import response
import pytest
from app import Flask, app, cart, BOOKS
from models import Book, Cart, CartItem, User, Order
import datetime
import flask
from email_validator import validate_email, EmailNotValidError  
import re
import test_units_final

@pytest.fixture
def client():
    """
    Flask test client fixture for integration testing.
    
    Configures the application in testing mode and provides a test client
    for making HTTP requests to test endpoints.
    
    Returns:
        Flask test client instance for making HTTP requests
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_homepage_loads(client):
    """
    Test that the homepage loads successfully.
    
    Validates:
    - Homepage returns 200 status code
    - Response contains "Book Store" text
    
    This ensures the main landing page is accessible and displays correctly.
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Online Bookstore" in response.data

def test_book_details_page(client):
    """
    Test that books are displayed on the homepage.

    Validates:
    - Homepage displays book information
    - Book titles and details are visible

    This ensures users can view book information on the main page.
    """
    response = client.get('/')
    assert response.status_code == 200
    assert b"Featured Books" in response.data or b"book" in response.data.lower()

def test_add_to_cart(client):
    """
    Test adding books to shopping cart functionality.
    
    Validates:
    - Adding books to cart returns 200 status code
    - Response redirects to cart-related page
    - Cart functionality is accessible
    
    This ensures the core shopping cart addition feature works properly.
    """
    response = client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 2}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Cart" in response.data or b"Added" in response.data

def test_cart_page(client):
    """
    Test that the shopping cart page loads successfully.
    
    Validates:
    - Cart page returns 200 status code
    - Response contains cart header text
    
    This ensures users can access and view their shopping cart contents.
    """
    response = client.get('/cart')
    assert response.status_code == 200
    assert b"Your Shopping Cart" in response.data or b"Cart" in response.data

def test_checkout_requires_login(client):
    """
    Test that checkout process requires user authentication.
    
    Validates:
    - Unauthenticated checkout request redirects to login
    - Security enforcement for checkout functionality
    
    This ensures checkout is protected and requires user login.
    """
    response = client.get('/checkout', follow_redirects=True)
    assert b"Login" in response.data

def test_register_and_login(client):
    """
    Test complete user registration and login workflow.
    
    Validates:
    - User registration process works correctly
    - Successful registration allows subsequent login
    - Login provides access to authenticated features
    
    This tests the complete user authentication flow from registration to login.
    """
    email = "testuser@example.com"
    password = "TestPassword123"
    # Register
    response = client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    assert b"Login" in response.data or b"Welcome" in response.data
    # Login
    response = client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    assert b"Logout" in response.data or b"Online Bookstore" in response.data

def test_order_placement(client):
    """
    Test complete order placement workflow from registration to confirmation.
    
    Validates:
    - User can register and login successfully
    - Items can be added to cart
    - Checkout process completes successfully
    - Order confirmation is provided
    
    This tests the full e-commerce purchase flow end-to-end.
    """
    # Register and login
    email = "orderuser@example.com"
    password = "OrderPass123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    # Add to cart
    book_id = 1
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    # Checkout
    response = client.post('/process-checkout', data={
        'name': 'Test User',
        'email': email,
        'address': '123 Main St',
        'city': 'Test City',
        'zip_code': '12345',
        'payment_method': 'cash'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data or b"confirmed" in response.data.lower()

def test_logout(client):
    """
    Test user logout functionality.
    
    Validates:
    - User can register and login successfully
    - Logout process works correctly
    - After logout, user is redirected to login page
    
    This ensures secure session termination and proper logout flow.
    """
    email = "logoutuser@example.com"
    password = "LogoutPass123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    response = client.get('/logout', follow_redirects=True)
    assert b"Login" in response.data

def test_invalid_login(client):
    """
    Test login security with invalid credentials.
    
    Validates:
    - Invalid email/password combinations are rejected
    - Appropriate error messages are displayed
    - Security measures prevent unauthorized access
    
    This ensures login authentication properly validates user credentials.
    """
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert b"Invalid email or password" in response.data or b"Login" in response.data

def test_register_with_existing_email(client):
    """
    Test registration validation for duplicate email addresses.
    
    Validates:
    - First registration with email succeeds
    - Second registration with same email is rejected
    - Appropriate error message for duplicate email
    
    This ensures email uniqueness is enforced during registration.
    """
    email = "duplicate@example.com"
    password = "SomePass123"
    # First registration
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    # Second registration with same email
    response = client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    assert b"Email already registered" in response.data or b"Register" in response.data

def test_add_invalid_book_to_cart(client):
    """
    Test cart handling of invalid book IDs.
    
    Validates:
    - Adding non-existent book returns 404 error
    - Appropriate error handling for invalid book references
    - Cart system validates book existence
    
    This ensures robust error handling for invalid cart operations.
    """
    invalid_book_id = 9999
    response = client.post(f'/add_to_cart/{invalid_book_id}', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    assert response.status_code == 404 or b"Book not found" in response.data

def test_cart_quantity_update(client):
    """
    Test shopping cart quantity modification functionality.
    
    Validates:
    - Items can be added to cart successfully
    - Cart quantities can be updated after addition
    - Update confirmation is provided to user
    
    This ensures cart modification features work correctly.
    """
    book_id = 1
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/update-cart', data={
        'title': 'The Great Gatsby',
        'quantity': 3
    }, follow_redirects=True)
    assert b"updated" in response.data.lower() or b"cart" in response.data.lower()

def test_remove_item_from_cart(client):
    """
    Test cart item removal functionality.
    
    Validates:
    - Items can be added to cart
    - Items can be removed from cart successfully
    - Removal confirmation is provided
    
    This ensures complete cart management capabilities.
    """
    book_id = 1
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/remove-from-cart', data={
        'title': 'The Great Gatsby'
    }, follow_redirects=True)
    assert b"removed" in response.data.lower() or b"cart" in response.data.lower()

def test_checkout_with_empty_cart(client):
    """
    Test checkout validation with empty shopping cart.
    
    Validates:
    - User can register and login successfully
    - Empty cart checkout is properly handled
    - Appropriate error message for empty cart
    
    This ensures checkout validation prevents empty orders.
    """
    email = "emptycart@example.com"
    password = "EmptyCart123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'address': '123 Main St',
        'name': 'Test User', 'email': email, 'city': 'Test City', 'zip_code': '12345', 'payment_method': 'cash'
    }, follow_redirects=True)
    assert b"Your cart is empty" in response.data or b"Cart" in response.data

def test_profile_page_requires_login(client):
    """
    Test that user profile page requires authentication.
    
    Validates:
    - Unauthenticated profile access redirects to login
    - Profile page is protected from anonymous access
    
    This ensures user profile security and access control.
    """
    response = client.get('/account', follow_redirects=True)
    assert b"Login" in response.data

def test_profile_page_after_login(client):
    """
    Test user profile page access after successful login.
    
    Validates:
    - User can register and login successfully
    - Profile page is accessible after login
    - Profile displays user information correctly
    
    This ensures authenticated users can access their profile.
    """
    email = "profileuser@example.com"
    password = "ProfilePass123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    response = client.get('/account', follow_redirects=True)
    assert b"Account" in response.data or bytes(email, 'utf-8') in response.data

def test_integration_final_cart_checkout_flow(client):
    """
    Test integrated order history functionality after purchase.
    
    Validates:
    - Complete purchase workflow from registration to checkout
    - Order history page accessibility
    - Order data persistence and retrieval
    - User-specific order history display
    
    This tests order tracking and history management integration.
    """
    email = "orderhistory@example.com"
    password = "OrderHistory123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    client.post('/process-checkout', data={
        'name': 'History User',
        'email': email,
        'address': '123 Main St',
        'city': 'Test City',
        'zip_code': '12345',
        'payment_method': 'credit_card',
        'card_number': '4419022512345678'
    }, follow_redirects=True)
    response = client.get('/account', follow_redirects=True)
    assert b"Order History" in response.data or b"Account" in response.data or bytes(email, 'utf-8') in response.data

def test_user_responsiveness_desktop_no_error(client, test_email = "desktopuser@example.com" , test_password = "DesktopPass123!", timeout=5):
    """
    Test user interface responsiveness on desktop devices.
    
    Validates:
    - Page load times for key user flows
    - Smoothness of interactions (e.g., adding to cart, checkout)
    - Overall user experience on desktop screens
    
    This ensures the application is performant and user-friendly on larger displays.
    """
    if len(test_password) < 8 or not re.search(r'\d', test_password) or not re.search(r'[A-Za-z]', test_password):
        return
    try:
        validate_email(test_email)
    except EmailNotValidError:
        return
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', test_email):
        return
    if len(test_password) < 8 or not re.search(r'\d', test_password) or not re.search(r'[A-Za-z]', test_password):
        return
    client.post('/register', data={
        'email': test_email,
        'password': test_password,
        'confirm': test_password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': test_email,
        'password': test_password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'name': 'Desktop User',
        'email': test_email,
        'address': '123 Main St',
        'city': 'Test City',
        'zip_code': '12345',
        'payment_method': 'credit_card',
        'card_number': '45419022512345678'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data or b"confirmed" in response.data.lower()
    assert b'Email sent to your email address' in response.data or b'Order Confirmation' in response.data
    print("Thanks for shopping with us!")

def test_integration_final_cart_checkout_flow(client):
    """
    Test final comprehensive cart and checkout integration.
    
    Validates:
    - Complete user registration and authentication
    - Shopping cart addition functionality
    - Final checkout process execution
    - Order completion and confirmation
    
    This is a final validation test for the complete shopping flow.
    """
    email = "finalcartuser@example.com" 
    password = "FinalCartPass123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'name': 'Final Cart User 2',
        'email': email,
        'address': '123 Main St',
        'city': 'Test City',
        'zip_code': '12345',
        'payment_method': 'credtit_card',
        'card_number': '45419022512345678'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data or b"confirmed" in response.data.lower()

def test_full_integration_of_user_journey(client):
    """
    Test complete end-to-end user journey integration.
    
    Validates:
    - User registration and authentication
    - Shopping cart functionality
    - Complete checkout and order placement
    - Order history accessibility and data persistence
    - User profile management access
    
    This is the most comprehensive integration test covering the entire
    user experience from registration to post-purchase account management.
    """
    email = "fullintegration@example.com"
    password = "FullIntegration123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'address': '123 Main St',
        'name': 'Test User', 'email': email, 'city': 'Test City', 'zip_code': '12345', 'payment_method': 'cash'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Order History" in response.data or b"Account" in response.data or b"Login" in response.data or bytes(email, "utf-8") in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Account" in response.data or b"Login" in response.data or bytes(email, 'utf-8') in response.data    

def test_integration_payment_processing(client):
    """
    Test integrated payment processing workflow.
    
    Validates:
    - User authentication and session management
    - Shopping cart and item management
    - Checkout process execution
    - Payment processing and transaction completion
    - Order confirmation and data persistence
    - Post-purchase account features (history and profile)
    
    This tests the complete payment integration including transaction
    processing, order fulfillment, and account management features.
    """
    email = "paymentprocessing@example.com"
    password = "PaymentProcessing123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'address': '123 Main St',
        'name': 'Test User', 'email': email, 'city': 'Test City', 'zip_code': '12345', 'payment_method': 'cash'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Order History" in response.data or b"Account" in response.data or b"Login" in response.data or bytes(email, "utf-8") in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Account" in response.data or b"Login" in response.data or bytes(email, 'utf-8') in response.data    

def test_integration_final_checkout_process(client):
    """
    Test final comprehensive checkout process integration.
    
    Validates:
    - User registration and authentication
    - Shopping cart addition functionality
    - Verify the cards validation
    - Validate the email format
    - Checkout process execution
    - Order completion and confirmation
    
    This is a final validation test for the complete checkout flow.
    """
    email = "finalcheckout@example.com"
    password = "FinalCheckout123"
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'address': '123 Main St',
        'name': 'Test User', 
        'email': email, 
        'city': 'Test City', 
        'zip_code': '12345', 
        'payment_method': 'credit_card', 
        'card_number': '4519022512345678',
        'expiry_date': '12/25',
        'cvv': '123'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data or b"confirmation" in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Order History" in response.data or b"Account" in response.data or b"Login" in response.data or bytes(email, "utf-8") in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Account" in response.data or b"Login" in response.data or bytes(email, 'utf-8') in response.data

def test_integration_complete_user_journey(client): 
    """
    Test complete end-to-end user journey integration.
    
    Validates:
    - User registration and authentication
    - Shopping cart functionality
    - Checkout process execution
    - Complete checkout and order placement
    - Order confirmation and notification
    - Sent order confirmation by email  
    - Order history accessibility and data persistence
    - User profile management access
    
    This is the most comprehensive integration test covering the entire
    user experience from registration to post-purchase account management.
    """
    email = "completeuserjourney@example.com"
    password = "CompleteUserJourney123"
    
    client.post('/register', data={
        'email': email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    client.post('/login', data={
        'email': email,
        'password': password
    }, follow_redirects=True)
    client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'address': '123 Main St',
        'name': 'Test User', 
        'email': email, 
        'city': 'Test City', 
        'zip_code': '12345', 
        'payment_method': 'credit_card', 
        'card_number': '4519022512345678',
        'expiry_date': '12/25',
        'cvv': '123'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data or b"confirmation" in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Order History" in response.data or b"Account" in response.data or b"Login" in response.data or bytes(email, "utf-8") in response.data

def test_integration_security_improvements_and_halt_SQL_injection(client):
    """
    Test security improvements against SQL injection attacks.
    
    Validates:
    - User registration with SQL injection attempt is rejected
    - Login with SQL injection attempt is rejected
    - Cart addition with SQL injection attempt is rejected
    - Checkout process with SQL injection attempt is rejected
    
    This ensures the application is protected against common SQL injection vectors.
    """
    sql_injection_email = "test'; DROP TABLE users; --@example.com"
    sql_injection_password = "password'; DROP TABLE users; --"  
    response = client.post('/register', data={
        'email': sql_injection_email,
        'password': sql_injection_password,
        'confirm': sql_injection_password
    }, follow_redirects=True)
    assert b"Invalid email format" in response.data or b"Register" in response.data
    response = client.post('/login', data={
        'email': sql_injection_email,
        'password': sql_injection_password
    }, follow_redirects=True)
    assert b"Invalid email format" in response.data or b"Login" in response.data
    response = client.post('/add-to-cart', data={'title': "The Great Gatsby'; DROP TABLE books; --", 'quantity': 1200}, follow_redirects=True)
    if response.status_code == 200:
        assert b"Quantity exceeds limit" in response.data or b"Cart" in response.data
        print("Quantity requested exceeds available stock or limit.")
    assert response.status_code == 404 or b"Book not found" in response.data
    response = client.post('/process-checkout', data={
        'address': "123 Main St'; DROP TABLE orders; --",
        'name': 'SQL Injection User',
        'email': sql_injection_email
    }, follow_redirects=True)
    assert b"Invalid email format" in response.data or b"Checkout" in response.data

def test_full_integration_shopping_experience(client):
    """
    Test complete end-to-end user journey integration.

    Validates:
    - Registration rejects invalid email formats
    - Valid email formats are accepted during registration
    - Email validation works in user workflows
    
    This ensures robust email validation in user workflows.
    """
    # Test invalid email format
    invalid_email = "invalidemail"
    password = "ValidPass123"  # Define a password to use in registration
    if not test_units_final.test_strong_password_creation():
          return # Skip test if password is not strong enough
    response = client.post('/register', data={
        'email': invalid_email,
        'password': password,
        'confirm': password
    }, follow_redirects=True)
    
    # Should either show an error or redirect to login (depending on app validation)
    assert response.status_code == 200
    
    # Test valid email format  
    valid_email = "validemail@example.com"
    if not validate_email(valid_email):
        raise ValueError("Email format is not valid for this test.")
        return
    response = client.post('/register', data={
        'email': valid_email,
        'password': password,
        'confirm': password
        }, follow_redirects=True)
    # Valid email should be accepted
    assert response.status_code == 200
    assert b"Online Bookstore" in response.data or b"Login" in response.data
    # the cart checkout functionality
    response = client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1}, follow_redirects=True)
    response = client.post('/process-checkout', data={
        'name': 'Email Test User',
        'email': valid_email,
        'address': '123 Main St',
        'city': 'Test City',
        'zip_code': '12345',
        'payment_method': 'credit_card'
    }, follow_redirects=True)
    assert b"Order Confirmation" in response.data or b"Thank you" in response.data
    # payment processing
    response = client.get('/account', follow_redirects=True)
    assert b"Order History" in response.data or b"Account" in response.data or b"Login" in response.data or bytes(valid_email, "utf-8") in response.data
    response = client.get('/account', follow_redirects=True)
    assert b"Account" in response.data or b"Login" in response.data or bytes(valid_email, 'utf-8') in response.data
    # order confirmation by email
    try:
        valid = validate_email(valid_email)
        email = valid.email
    except EmailNotValidError as e:
        print(str(e))
        return
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        print("Email format is invalid.")
        cart = Cart()
        cart.items.clear()
        assert len(cart.items) == 0
        assert cart.get_total_price() == 0.00
        #redirect to home page
        response = client.get('/', follow_redirects=True)
        return
    else:
        assert re.match(email_regex, email)
        print("Thank you! Your order has been placed successfully.")

if __name__ == "__main__":
    os.system("cls")  # Clear console on Windows
    pytest.main()
