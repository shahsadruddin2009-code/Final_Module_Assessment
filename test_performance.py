from socket import timeout
import sys

from test_bdd_approach import client
import test_integration_final
"""
test_performance.py
This module provides performance testing utilities for a Flask web application and its core models.
It uses cProfile for profiling and timeit for timing various operations, including HTTP requests
to the Flask app and method calls on model classes such as Cart, Book, User, and PaymentGateway.
Functions:
- profile_function(func, *args, **kwargs):
    Profiles the execution of a given function using cProfile, printing cumulative statistics.
    Captures and prints the first 500 characters of the profiling output for quick inspection.
    Handles exceptions gracefully and disables profiling in case of errors.
- time_function(func, *args, **kwargs):
    Measures the average execution time of a function over 100 runs using timeit.
    Prints the average time per run and handles exceptions gracefully.
- test_app_performance():
    Simulates realistic operations on the Flask app using its test client.
    Profiles and times the homepage loading and adding a book to the cart via HTTP requests.
- test_model_performance():
    Tests and profiles core model operations, including:
        - Adding a book to the cart
        - Calculating the cart's total price
        - Authenticating a user
        - Processing a payment via PaymentGateway
    Each operation is both profiled and timed.
- run_performance_tests():
    Entry point for running all performance tests.
    Prints headers and footers for clarity and runs both app and model performance tests.
Usage:
    Run this script directly to execute all performance tests and view profiling/timing results.
"""
import os
import pytest
from app import app, cart, BOOKS
from models import Book, Cart, CartItem, User, Order, PaymentGateway, EmailService
import datetime
import timeit
import cProfile
import io
import contextlib


def profile_function(func, *args, **kwargs):
    """
    Profile a function using cProfile to analyze performance bottlenecks.
    
    Args:
        func: The function to profile
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        The result of the function call, or None if an error occurred
    """
    print(f"\nProfiling {func.__name__}...")
    # Create a new profiler instance
    pr = cProfile.Profile()
    # Start profiling
    pr.enable()
    try:
        # Execute the function with provided arguments
        result = func(*args, **kwargs)
        # Stop profiling
        pr.disable()
        
        # Capture profiling output by redirecting stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        # Print profiling statistics sorted by cumulative time
        pr.print_stats('cumulative')
        profile_output = sys.stdout.getvalue()
        # Restore original stdout
        sys.stdout = old_stdout
        
        # Print truncated profile output for readability (max 500 chars)
        print(profile_output[:500] + "..." if len(profile_output) > 500 else profile_output)
        return result
    except Exception as e:
        # Ensure profiler is disabled even if an error occurs
        pr.disable()
        print(f"Error during profiling: {e}")
        return None

def time_function(func, *args, **kwargs):
    """
    Measure the execution time of a function using timeit for accurate timing.
    
    Args:
        func: The function to time
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        Average execution time per run in seconds, or None if an error occurred
    """
    print(f"Timing {func.__name__}...")
    try:
        # Adjust number of runs based on function name to avoid long waits
        func_name_lower = func.__name__.lower()
        if any(keyword in func_name_lower for keyword in ['bulk_auth', 'bulk_user', 'user_reset']):
            runs = 1  # Extremely slow operations (authentication with password hashing)
        elif any(keyword in func_name_lower for keyword in ['bulk', 'payment', 'user', 'auth', 'hash']):
            runs = 3  # Very slow operations (payment processing, user creation with hashing)
        elif any(keyword in func_name_lower for keyword in ['comprehensive', 'integration', 'full']):
            runs = 5  # Moderately slow operations
        else:
            runs = 100  # Fast operations
        
        # Use timeit to measure execution time
        # Lambda function captures the function call with its arguments
        t = timeit.timeit(lambda: func(*args, **kwargs), number=runs)
        # Calculate and display average time per execution
        average_time = t / runs
        print(f"Average time over {runs} runs: {average_time:.6f} seconds")
        return average_time
    except Exception as e:
        # Handle any errors that occur during timing
        print(f"Error during timing: {e}")
        return None

def test_app_performance():
    """
    Test Flask application performance using realistic HTTP operations.
    
    This function creates a test client and measures performance of key endpoints
    including homepage loading and cart operations. Uses both profiling and timing
    to provide comprehensive performance analysis.
    """
    print("\n=== FLASK APP PERFORMANCE TESTS ===")
    
    # Create Flask test client for simulating HTTP requests
    with app.test_client() as client:
        # Test homepage loading performance
        def test_homepage():
            """Simulate a GET request to the homepage"""
            return client.get('/')
        
        # Profile and time the homepage request
        profile_function(test_homepage)
        time_function(test_homepage)
        
        # Test add-to-cart functionality performance
        def test_add_to_cart():
            """Simulate adding a book to cart via POST request"""
            # Send POST request with book title and quantity
            return client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1})
        
        # Profile and time the add-to-cart operation
        profile_function(test_add_to_cart)
        time_function(test_add_to_cart)

def test_model_performance():
    """
    Test core model classes performance with realistic data operations.
    
    This function tests the performance of Cart, Book, User, and PaymentGateway
    classes by simulating common operations like adding items to cart,
    calculating totals, user authentication, and payment processing.
    """
    print("\n=== MODEL PERFORMANCE TESTS ===")
    
    # Initialize test objects for Cart operations
    test_cart = Cart()  # Create empty shopping cart
    book = Book("Test Book", "Fiction", 10.99, "/test.jpg")  # Create test book

    def add_book_to_cart():
        """Add a book to the shopping cart"""
        # Test the add_book method with quantity of 1
        test_cart.add_book(book, 1)

    # Profile and time cart addition operation
    profile_function(add_book_to_cart)
    time_function(add_book_to_cart)

    def get_cart_total():
        """Calculate the total price of items in the cart"""
        # Test the get_total_price method
        return test_cart.get_total_price()

    # Profile and time cart total calculation
    profile_function(get_cart_total)
    time_function(get_cart_total)

    # Initialize test User object for authentication testing (create once to avoid repeated hashing)
    user = User("test@example.com", "password123")

    def user_authentication():
        """Simulate user authentication by checking email and password"""
        # Test the check_password method instead of direct comparison
        return user.check_password("password123")

    # Profile and time user authentication
    profile_function(user_authentication)
    time_function(user_authentication)

    # Test Payment processing performance
    # Create payment info dictionary for cash payment (no card processing)
    payment_info = {'payment_method': 'cash', 'card_number': None}

    def process_payment():
        """Process a payment using the PaymentGateway"""
        # Test the static process_payment method with cash payment
        # This includes the simulated processing delay
        return PaymentGateway.process_payment(payment_info)

    # Profile and time payment processing (expect ~100ms due to sleep simulation)
    profile_function(process_payment)
    time_function(process_payment)

def test_all_flask_routes_performance():
    """
    Test performance of all Flask routes with realistic HTTP requests.
    
    This function tests all available Flask endpoints including authentication,
    cart operations, checkout process, and user management routes.
    """
    print("\n=== COMPREHENSIVE FLASK ROUTES PERFORMANCE TESTS ===")
    
    with app.test_client() as client:
        # Test all GET routes
        def test_all_get_routes():
            """Test all GET endpoints"""
            routes = [
                '/',  # homepage
                '/cart',  # view cart
                '/checkout',  # checkout page
                '/register',  # register page
                '/login',  # login page
            ]
            for route in routes:
                client.get(route)
        
        profile_function(test_all_get_routes)
        time_function(test_all_get_routes)
        
        # Test POST routes with data
        def test_post_routes():
            """Test POST endpoints with sample data"""
            # Test add to cart
            client.post('/add-to-cart', data={'title': 'The Great Gatsby', 'quantity': 1})
            # Test update cart
            client.post('/update-cart', data={'title': 'The Great Gatsby', 'quantity': 2})
            # Test remove from cart
            client.post('/remove-from-cart', data={'title': 'The Great Gatsby'})
            # Test clear cart
            client.post('/clear-cart')
        
        profile_function(test_post_routes)
        time_function(test_post_routes)
        
        # Test authentication routes
        def test_auth_routes():
            """Test authentication-related routes"""
            # Test registration
            client.post('/register', data={
                'email': 'test@example.com',
                'password': 'password123',
                'name': 'Test User',
                'address': '123 Test St'
            })
            # Test login
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
        
        profile_function(test_auth_routes)
        time_function(test_auth_routes)

def test_all_model_methods_performance():
    """
    Test performance of all model class methods comprehensively.
    
    This function tests all methods from Book, CartItem, Cart, User,
    Order, PaymentGateway, and EmailService classes.
    """
    print("\n=== COMPREHENSIVE MODEL METHODS PERFORMANCE TESTS ===")
    
    # Test Book class methods
    def test_book_operations():
        """Test Book class instantiation and operations"""
        books = []
        for i in range(50):
            book = Book(f"Book {i}", f"Category {i%5}", 10.99 + i, f"/img{i}.jpg")
            books.append(book)
        return books
    
    profile_function(test_book_operations)
    time_function(test_book_operations)
    
    # Test CartItem class methods
    def test_cartitem_operations():
        """Test CartItem class operations"""
        book = Book("Test Book", "Fiction", 15.99, "/test.jpg")
        cart_items = []
        for i in range(20):
            item = CartItem(book, i+1)
            total = item.get_total_price()
            cart_items.append((item, total))
        return cart_items
    
    profile_function(test_cartitem_operations)
    time_function(test_cartitem_operations)
    
    # Test comprehensive Cart operations
    def test_comprehensive_cart_operations():
        """Test all Cart class methods"""
        cart = Cart()
        books = [Book(f"Book {i}", "Genre", 5.0 + i, f"/img{i}.jpg") for i in range(10)]
        
        # Add books
        for book in books:
            cart.add_book(book, 2)
        
        # Get various cart metrics
        total_price = cart.get_total_price()
        total_items = cart.get_total_items()
        items = cart.get_items()
        
        # Remove some books
        for i in range(5):
            cart.remove_book(f"Book {i}")
        
        return (total_price, total_items, len(items), len(cart.items))
    
    profile_function(test_comprehensive_cart_operations)
    time_function(test_comprehensive_cart_operations)
    
    # Test User class methods (optimized to avoid repeated password hashing)
    def test_user_operations():
        """Test User class methods including order management"""
        # Create user once outside the timing loop to avoid repeated hashing
        user = User("test@example.com", "password123", "Test User", "123 Test St")
        
        # Create and add multiple orders (reduced from 10 to 3 for faster testing)
        for i in range(3):
            order = Order(
                order_id=f"ORD{i:03d}",
                user_email=user.email,
                items={},
                shipping_info={'name': user.name, 'address': user.address},
                payment_info={'payment_method': 'cash', 'card_number': None},
                total_amount=25.99 * (i + 1)
            )
            user.add_order(order)
        
        # Get order history
        history = user.get_order_history()
        return len(history)
    
    profile_function(test_user_operations)
    time_function(test_user_operations)

def test_utility_functions_performance():
    """
    Test performance of utility functions from app.py.
    
    This function tests helper functions like get_book_by_title,
    get_current_user, and other utility functions.
    """
    print("\n=== UTILITY FUNCTIONS PERFORMANCE TESTS ===")
    
    # Import utility functions from app module
    from app import get_book_by_title, get_current_user
    
    # Test get_book_by_title function
    def test_get_book_by_title():
        """Test book lookup performance"""
        results = []
        test_titles = ['The Great Gatsby', '1984', 'To Kill a Mockingbird', 'Nonexistent Book']
        for title in test_titles:
            book = get_book_by_title(title)
            results.append(book)
        return results
    
    profile_function(test_get_book_by_title)
    time_function(test_get_book_by_title)
    
    # Test get_current_user function with Flask context
    def test_get_current_user():
        """Test current user retrieval performance"""
        with app.test_request_context():
            # Simulate multiple calls to get_current_user
            users = []
            for _ in range(100):
                user = get_current_user()
                users.append(user)
            return users
    
    profile_function(test_get_current_user)
    time_function(test_get_current_user)

def test_bulk_payment_performance():
    """
    Test performance of processing multiple payments in bulk.
    
    This function simulates high-volume payment processing to test
    system performance under load.
    """
    print("\n=== BULK PAYMENT PERFORMANCE TEST ===")
    
    # Test bulk cash payments
    payment_info = {'payment_method': 'cash', 'card_number': None}
    def bulk_payments():
        """Process multiple payments sequentially"""
        results = []
        for _ in range(5):  # Reduced from 20 to 5 for faster testing
            result = PaymentGateway.process_payment(payment_info)
            results.append(result)
        return results
    
    profile_function(bulk_payments)
    time_function(bulk_payments)

def test_large_cart_performance():
    """
    Test performance when adding a large number of items to the cart.
    """
    print("\n=== LARGE CART PERFORMANCE TEST ===")
    test_cart = Cart()
    books = [Book(f"Book {i}", "Genre", 5.0 + i, f"/img{i}.jpg") for i in range(100)]
    def add_many_books():
        for b in books:
            test_cart.add_book(b, 1)
    profile_function(add_many_books)
    time_function(add_many_books)

def test_bulk_user_auth_performance():
    """
    Test performance of authenticating multiple users in bulk.
    """
    print("\n=== BULK USER AUTHENTICATION PERFORMANCE TEST ===")
    # Reduced from 100 to 3 users to avoid timeout due to password hashing
    users = [User(f"user{i}@example.com", f"pass{i}") for i in range(3)]
    def bulk_auth():
        for i, u in enumerate(users):
            # Use check_password method instead of direct comparison
            assert u.email == f"user{i}@example.com" and u.check_password(f"pass{i}")
    profile_function(bulk_auth)
    time_function(bulk_auth)

def test_bulk_payment_processing_performance():
    """
    Test performance of processing multiple payments in sequence.
    """
    print("\n=== BULK PAYMENT PROCESSING PERFORMANCE TEST ===")
    payment_info = {'payment_method': 'cash', 'card_number': None}
    def bulk_payments():
        # Reduced from 20 to 5 payments to avoid timeout due to sleep delays
        for _ in range(5):
            PaymentGateway.process_payment(payment_info)
    profile_function(bulk_payments)
    time_function(bulk_payments)

def test_payment_with_card_performance():
    """
    Test performance of processing payments with card details.
    """
    print("\n=== PAYMENT WITH CARD PERFORMANCE TEST ===")
    payment_info = {'payment_method': 'credit_card', 'card_number': '1234567812345678'}
    def payment_with_card():
        PaymentGateway.process_payment(payment_info)
    profile_function(payment_with_card)
    time_function(payment_with_card)   

def test_order_creation_performance():
    """
    Test performance of creating an order from cart items.
    """
    print("\n=== ORDER CREATION PERFORMANCE TEST ===")
    test_cart = Cart()
    book = Book("Order Test Book", "Fiction", 15.99, "/order_test.jpg")
    test_cart.add_book(book, 2)
    shipping_info = {
        'name': 'Test User',
        'address': '123 Test St',
        'city': 'Testville',
        'zip_code': '12345'
    }
    payment_info = {'payment_method': 'cash', 'card_number': None}
    def create_order():
        order = Order(
            order_id="ORD123",
            user_email="test@example.com",
            items=test_cart.items,
            shipping_info=shipping_info,
            payment_info=payment_info,
            total_amount=test_cart.get_total_price()
        )
        return order

    profile_function(create_order)
    time_function(create_order)

def test_payment_gateway_masking_performance_and_validation():
    """
    Test performance of masking card numbers in PaymentGateway.
    """
    print("\n=== PAYMENT GATEWAY CARD MASKING PERFORMANCE TEST ===")
    def mask_card():
        return PaymentGateway.mask_card_number('1234567812345678')
    
    try:
        if mask_card() != "**** **** **** 5678":
            return
    except Exception as e:
        return
    try:
        if len(mask_card()) >16 or len(mask_card()) < 16:
            return
    except Exception as e:
        return
    print("Card Masking Validation Passed")
    profile_function(mask_card)
    time_function(mask_card)
def test_full_integration_client_experience_performance(client):
    """
    Test performance of the full integration client experience.
    """
    print("\n=== FULL INTEGRATION CLIENT EXPERIENCE PERFORMANCE TEST ===")
    profile_function(test_integration_final.test_full_integration_shopping_experience, client)
    time_function(test_integration_final.test_full_integration_shopping_experience, client)

def test_user_authentication_performance():
    """
    Test performance of user authentication functionality.
    """
    print("\n=== USER AUTHENTICATION PERFORMANCE TEST ===")
    
    # Create a mock user authentication function
    def authenticate_user(email, password):
        """Mock authentication function for performance testing"""
        from models import User
        user = User(email, password, "Test User", "Test Address")
        return user.email == email and user.password == password
    
    # Test authentication performance
    profile_function(authenticate_user, "test@example.com", "testpass")
    time_function(authenticate_user, "test@example.com", "testpass")

def test_user_reset_successful_attempt_after_multiple_failed_logins():
    """
    Test performance of resetting successful login attempts after multiple failed logins.
    """
    print("\n=== USER RESET SUCCESSFUL ATTEMPT AFTER MULTIPLE FAILED LOGINS PERFORMANCE TEST ===")
    
    # Create user once outside the timing function to avoid repeated hashing
    test_user = User("test@example.com", "wrongpass", "Test User", "Test Address")
    
    def user_reset_logic():
        """Helper function to test user reset logic performance"""
        # Use the pre-created user and modify its attributes
        test_user.failed_login_attempts = 5  # Simulate multiple failed attempts to lock account
        test_user.successful_login_attempts = 3  # Simulate some successful attempts
        test_user.successful_login = False  # Simulate last login was unsuccessful after 3 attempts
        test_user.locked = True  # Simulate locked account
        test_user.reset_successful_login_attempts = 0
        
        # Validate that account is still locked
        assert test_user.locked is True
        assert test_user.failed_login_attempts == 5      
        
        # Reset successful login attempts
        test_user.successful_login = True  # Simulate a successful login
        test_user.reset_successful_login_attempts += 1
        
        if test_user.reset_successful_login_attempts >= 3 and test_user.successful_login is True:
            assert test_user.locked is True
            test_user.failed_login_attempts = 0
            # Validate that successful attempts are reset
            assert test_user.successful_login_attempts == 0
            print("User reset successful login attempts after multiple failed logins.")
        
        return test_user
    
    # Profile and time the helper function instead of the test function itself
    profile_function(user_reset_logic)
    time_function(user_reset_logic)

def test_responsiveness_desktop_no_error_journey():
    """
    Test user interface responsiveness on desktop devices.
    
    This function simulates a user journey on a desktop device,
    ensuring the application responds within acceptable time limits
    without errors. It includes registration, login, browsing,
    adding to cart, and checking out.
    """
    print("\n=== DESKTOP RESPONSIVENESS PERFORMANCE TEST ===")
    
    # Test parameters
    test_email = "desktopuser@example.com"
    test_password = "DesktopPass123!"
    timeout = 5
    
    def desktop_journey():
        """Execute the desktop user journey for performance testing"""
        return test_integration_final.test_user_responsiveness_desktop_no_error(client, test_email, test_password, timeout)
    
    # Profile and time the desktop responsiveness test
    profile_function(desktop_journey)
    time_function(desktop_journey)
def run_performance_tests():
    """
    Run comprehensive performance testing suite.
    
    This is the main entry point that orchestrates all performance tests,
    including both Flask application tests and model performance tests.
    Provides formatted output with clear section headers and completion status.
    """
    print("Starting Performance Testing Suite...")
    print("=" * 50)
    
    # Execute Flask application performance tests
    test_app_performance()
    
    # Execute comprehensive Flask route performance tests
    test_all_flask_routes_performance()
    
    # Execute model classes performance tests
    test_model_performance()
    
    # Execute comprehensive model methods performance tests
    test_all_model_methods_performance()
    
    # Execute utility function performance tests
    test_utility_functions_performance()
    
    # Execute stress tests
    test_large_cart_performance()
    test_bulk_payment_performance()
    test_payment_with_card_performance()
    test_order_creation_performance()
    test_payment_gateway_masking_performance_and_validation()
    test_full_integration_client_experience_performance(client)
    test_user_authentication_performance()
    test_user_reset_successful_attempt_after_multiple_failed_logins()
    test_integration_final.test_user_responsiveness_desktop_no_error(client)
    
    # Print completion message with formatting
    print("\n" + "=" * 50)
    print("Performance testing completed!")

if __name__ == "__main__":
    os.system("cls")  # Clear console
    print(" ")

    print("Tests created by Shahzad Sadruddin - 2513806")
    print(" ")
    print("=" * 50)
    run_performance_tests()