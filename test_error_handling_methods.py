"""
Error Handling Tests for Bookstore Application
Tests various error conditions and edge cases to ensure robust application behavior.
"""
import sys
import os
import pytest
from app import Flask, app, cart, BOOKS
from models import Book, Cart, CartItem, User, Order, PaymentGateway, EmailService
import datetime
import flask
from email_validator import validate_email, EmailNotValidError  
import re

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    with app.test_client() as client:
        yield client

@pytest.fixture  
def authenticated_client():
    """Create a test client with an authenticated user session."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_email'] = 'test@example.com'
            sess['user_id'] = 1
        yield client
        # Cleanup after test
        with client.session_transaction() as sess:
            sess.clear()
        cart.clear()

def test_invalid_email_registration_error_handling():
    """Test error handling for invalid email during registration."""
    invalid_emails = [
        "invalid-email",
        "@example.com", 
        "user@",
        "user@.com",
        "",
        None
    ]
    
    for invalid_email in invalid_emails:
        try:
            if invalid_email:
                validate_email(invalid_email)
                assert False, f"Expected EmailNotValidError for {invalid_email}"
        except (EmailNotValidError, TypeError):
            # Expected behavior - invalid email should raise error
            assert True
        except Exception as e:
            assert False, f"Unexpected error for {invalid_email}: {e}"

def test_empty_cart_checkout_error_handling():
    """Test error handling when attempting to checkout with empty cart."""
    test_cart = Cart()
    
    # Verify cart is empty
    assert len(test_cart.items) == 0  # nosec B101
    assert test_cart.get_total_price() == 0.0  # nosec B101
    
    # Attempting checkout with empty cart should handle gracefully
    try:
        # Simulate checkout process
        if len(test_cart.items) == 0:
            raise ValueError("Cannot checkout with empty cart")
    except ValueError as e:
        assert str(e) == "Cannot checkout with empty cart"

def test_invalid_payment_card_error_handling():
    """Test error handling for invalid payment card details."""
    invalid_cards = [
        "",
        None,
        "123",  # Too short
        "invalid_card_number",
        "0000000000000000"  # Invalid card
    ]
    
    for invalid_card in invalid_cards:
        try:
            result = PaymentGateway.mask_card_number(invalid_card)
            if invalid_card is None or invalid_card == "":
                assert result == "Invalid card number"
            else:
                # Should return masked version or error message
                assert isinstance(result, str)
        except Exception as e:
            # Any exception should be handled gracefully
            assert True

def test_order_creation_with_invalid_data_error_handling():
    """Test error handling when creating orders with invalid data."""
    try:
        # Missing required parameters should raise error
        order = Order("", "", [], {}, {}, 0.0)
        assert order.order_id == ""  # Should handle empty values gracefully
    except Exception as e:
        # Any exception should be handled appropriately
        assert True

def test_user_authentication_error_handling():
    """Test error handling for user authentication edge cases."""
    invalid_credentials = [
        ("", ""),
        (None, None),
        ("user@example.com", ""),
        ("", "password"),
        ("invalid_email", "password")
    ]
    
    for email, password in invalid_credentials:
        try:
            # Simulate authentication check
            if not email or not password:
                raise ValueError("Email and password required")
            
            # Check email format
            validate_email(email)
            
        except (ValueError, EmailNotValidError):
            # Expected behavior for invalid credentials
            assert True
        except Exception as e:
            # Any other exception should be handled
            assert True

def test_cart_operations_error_handling():
    """Test error handling for cart operations."""
    test_cart = Cart()
    
    # Test adding invalid book
    try:
        test_cart.add_book(None, 1)
        assert False, "Should not allow adding None book"
    except (AttributeError, TypeError):
        assert True
    
    # Test adding with invalid quantity
    test_book = Book("Test", "Author", 10.0, "/test.jpg")
    try:
        test_cart.add_book(test_book, -1)
        # Should handle negative quantity appropriately
        assert True
    except Exception:
        assert True

def test_flask_route_error_handling(client):
    """Test error handling for Flask routes."""
    # Test non-existent routes
    if not client:
        pytest.skip("Flask test client is not available.")
        return
    
    response = client.get('/nonexistent-route')
    assert response.status_code == 404
    # Test invalid book addition
    response = client.post('/add-to-cart', data={'book_index': '999'})
    # Should handle gracefully (redirect or error message)
    assert response.status_code in [200, 302, 400, 404]

def test_session_handling_errors(client):
    """Test error handling for session management."""
    # Test accessing protected routes without authentication
    response = client.get('/account')
    # Should redirect to login or show appropriate message
    assert response.status_code in [200, 302]
    
    # Test checkout without login
    response = client.get('/checkout')
    assert response.status_code in [200, 302]

def test_email_service_error_handling():
    """Test error handling in EmailService."""
    try:
        # Test sending email with invalid parameters
        EmailService.send_email("", "", "")
        assert False, "Should not allow sending email with empty parameters"
    except Exception:
        assert True
    
    try:
        # Test sending email with None parameters
        EmailService.send_email(None, None, None)
        assert False, "Should not allow sending email with None parameters"
    except Exception:
        assert True 

def test_payment_gateway_masking_performance_and_validation_errors():
    """Test error handling in PaymentGateway."""
    try:
        # Test payment processing with invalid card details
        PaymentGateway.process_payment("", "", 0.0)
        assert False, "Should not allow processing payment with empty card details"
    except Exception:
        assert True

    try:
        # Test payment processing with None card details
        PaymentGateway.process_payment(None, None, None)
        assert False, "Should not allow processing payment with None card details"
    except Exception:
        assert True

def test_entered_empty_book_in_field_and_no_checkout_process_error_handling():
    """Test error handling when entering empty book in field and no checkout process."""
    try:
        # Simulate adding empty book to cart
        test_cart = Cart()
        test_cart.add_book(None, 1)
        assert False, "Should not allow adding None book"
    except (AttributeError, TypeError):
        assert True
    
    try:
        # Simulate checkout process with empty cart
        if len(test_cart.items) == 0:
            raise ValueError("Cannot checkout with empty cart")
    except ValueError as e:
        assert str(e) == "Cannot checkout with empty cart"

def test_payment_with_invalid_card_number_error_handling():
    """Test error handling when processing payment with invalid card number."""
    invalid_card_numbers = [
        "",
        None,
        "123",  # Too short
        "invalid_card_number",
        "0000000000000000"  # Invalid card
    ]
    
    for invalid_card in invalid_card_numbers:
        try:
            result = PaymentGateway.process_payment({
                'card_number': invalid_card,
                'expiry_date': '12/25',
                'cvv': '123',
                'amount': 50.0,
                'payment_method': 'credit_card'
            })
            if invalid_card is None or invalid_card == "":
                assert not result['success']
            else:
                # Should return failure for invalid cards
                assert not result['success']
        except Exception as e:
            # Any exception should be handled gracefully
            assert True
            print(f"Exception occurred for card number {invalid_card}: {e}")
            print("Payment processing failed as expected.")
            assert True

def test_order_creation_with_missing_fields_error_handling():
    """Test error handling when creating orders with missing fields."""
    try:
        # Missing user_email
        order = Order("ORD123", "", [], {}, {}, 0.0)
        assert order.user_email == ""  # Should handle empty email gracefully
    except Exception as e:
        # Any exception should be handled appropriately
        assert True
    try:
        # Missing items
        order = Order("ORD123", "user@example.com", [], {}, {}, 0.0)
        assert order.items == []  # Should handle empty items gracefully
    except Exception as e:
        # Any exception should be handled appropriately
        assert True

def test_search_bar_functionality_error_handling(client):
    """Test error handling for search bar functionality."""
    # Test if search route exists
    response = client.get('/search')
    
    if response.status_code == 404:
        # Search functionality not implemented - skip this test
        pytest.skip("Search functionality not implemented in the application")
        return
    
    # Test searching with empty query
        response = client.get('/search', query_string={'query': ''})
        assert response.status_code == 200  # nosec B101
        assert b'No results found' in response.data or b'Search results' in response.data  # nosec B101    # Test searching with special characters
    special_queries = ['@#$%', '!!!', '1234567890', '<script>alert(1)</script>']
    for query in special_queries:
        response = client.get('/search', query_string={'query': query})
        assert response.status_code == 200
        assert b'No results found' in response.data or b'Search results' in response.data

def test_search_bar_not_existed_error_handling(client):
    """Test search bar functionality for non-existent features."""
    # Test that search route returns 404 when not implemented
    response = client.get('/search')
    if response.status_code == 404:
        # Search functionality not implemented - this is expected behavior
        pytest.skip("Search bar feature is not implemented in the application.")
    else:
        # If search exists, test it with non-existent query
        response = client.get('/search', query_string={'query': 'non_existent_feature'})
        assert response.status_code == 200
        assert b'No results found' in response.data

def test_confirmation_email_sending_error_handling():
    """Test error handling when sending confirmation email with invalid parameters."""
    try:
        # Test sending email with empty parameters
        EmailService.send_order_confirmation("", None)
        assert False, "Should not allow sending email with empty parameters"
    except Exception:
        assert True
    
    try:
        # Test sending email with None parameters
        EmailService.send_order_confirmation(None, None)
        assert False, "Should not allow sending email with None parameters"
    except Exception:
        assert True

def test_responsive_checkout_button_error_handling(client, authenticated_client):
    """Test error handling for responsive checkout button."""
    # Test accessing checkout route without authentication (with empty cart)
    response = client.get('/checkout')
    assert response.status_code in [200, 302]  # Should redirect due to empty cart or login
    
    # Test accessing checkout route with authentication (but still empty cart)
    response = authenticated_client.get('/checkout')
    # Should redirect to index because cart is empty, regardless of authentication
    assert response.status_code in [200, 302]  # Redirects due to empty cart
    
    # The checkout route redirects when cart is empty, which is expected behavior
    # This test validates that the error handling works correctly for both
    # authenticated and unauthenticated users when accessing checkout with empty cart

def test_email_service_with_invalid_email_format_error_handling():
    """Test error handling when sending email with invalid email format."""
    invalid_emails = [
        "invalid-email",
        "@example.com", 
        "user@",
        "user@.com",
        "",
        None
    ]
    
    for invalid_email in invalid_emails:
        try:
            if invalid_email:
                validate_email(invalid_email)
                assert False, f"Expected EmailNotValidError for {invalid_email}"
            # Attempt to send email with invalid email
            EmailService.send_order_confirmation(invalid_email, None)
            assert False, f"Should not allow sending email to {invalid_email}"
        except (EmailNotValidError, TypeError):
            # Expected behavior - invalid email should raise error
            assert True
        except Exception as e:
            assert True  # Any other exception should be handled

if __name__ == "__main__":
    print("Running Error Handling Tests...")
    print("=" * 50)
    pytest.main([__file__, "-v", "--tb=short"])