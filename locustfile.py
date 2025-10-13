from locust import HttpUser, TaskSet, task, between
import time
import os
import random
import cProfile
import io
import sys
import timeit
from contextlib import redirect_stdout

class BookstoreUserBehavior(TaskSet):
    """Simulates user behavior on the bookstore website"""
    
    def on_start(self):
        """Called when a user starts - simulates user arriving at the site"""
        print(f"User {self.user.user_id if hasattr(self.user, 'user_id') else 'anonymous'} started session")
    
    @task(3)
    def browse_homepage(self):
        """Browse the homepage - most common user action"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage failed with status {response.status_code}")
    
    @task(2)
    def view_books(self):
        """View book details - common user action"""
        book_ids = ["1", "2", "3", "4", "5"]  # Assuming we have books with these IDs
        book_id = random.choice(book_ids)
        with self.client.get(f"/book/{book_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Expected for non-existent books
            else:
                response.failure(f"Book view failed with status {response.status_code}")
    
    @task(2)
    def add_to_cart(self):
        """Add books to cart"""
        book_id = random.choice(["1", "2", "3"])
        quantity = random.randint(1, 3)
        with self.client.post("/add-to-cart", 
                            data={"book_id": book_id, "quantity": str(quantity)}, 
                            catch_response=True) as response:
            if response.status_code in [200, 302]:  # Success or redirect
                response.success()
            else:
                response.failure(f"Add to cart failed with status {response.status_code}")
    
    @task(1)
    def view_cart(self):
        """View shopping cart contents"""
        with self.client.get("/cart", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Cart view failed with status {response.status_code}")
    
    @task(1)
    def search_books(self):
        """Search for books"""
        search_terms = ["python", "programming", "science", "fiction", "history"]
        query = random.choice(search_terms)
        with self.client.get(f"/search?query={query}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed with status {response.status_code}")
    
    @task(1)
    def register_user(self):
        """Register a new user"""
        user_id = random.randint(1000, 9999)
        user_data = {
            "name": f"TestUser{user_id}",
            "email": f"test{user_id}@example.com",
            "password": "testpass123",
            "address": f"123 Test St, City {user_id}"
        }
        with self.client.post("/register", data=user_data, catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Registration failed with status {response.status_code}")
    
    def on_stop(self):
        """Called when user stops - cleanup"""
        print(f"User session ended")

class BookstoreUser(HttpUser):
    """Locust user class for bookstore load testing"""
    tasks = [BookstoreUserBehavior]
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    weight = 7  # 70% of users will be general browsers
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = random.randint(1, 10000)

# Additional load testing scenarios

class AuthenticatedUserBehavior(TaskSet):
    """Simulates authenticated user behavior"""
    
    def on_start(self):
        """Login user at start of session"""
        login_data = {
            "email": "test@example.com",
            "password": "testpass"
        }
        with self.client.post("/login", data=login_data, catch_response=True) as response:
            if response.status_code in [200, 302]:
                print("User logged in successfully")
            else:
                print(f"Login failed with status {response.status_code}")
    
    @task(2)
    def view_profile(self):
        """View user profile"""
        with self.client.get("/account", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile view failed")
    
    @task(3)
    def checkout_flow(self):
        """Simulate checkout process"""
        # First add item to cart
        self.client.post("/add-to-cart", data={"book_id": "1", "quantity": "1"})
        
        # Try to checkout
        with self.client.get("/checkout", catch_response=True) as response:
            if response.status_code in [200, 302]:
                response.success()
            else:
                response.failure(f"Checkout failed")

class AuthenticatedUser(HttpUser):
    """User class for authenticated user testing"""
    tasks = [AuthenticatedUserBehavior]
    wait_time = between(2, 8)
    weight = 2  # 20% of users will be authenticated

# Load testing configuration and scenarios

class BurstyUserBehavior(TaskSet):
    """Simulates bursty/peak traffic user behavior"""
    
    @task(5)
    def rapid_browsing(self):
        """Simulate rapid page browsing during peak times"""
        pages = ["/", "/cart", "/search?query=python"]
        for page in pages:
            self.client.get(page)
            time.sleep(0.1)  # Very short wait between requests
    
    @task(1)
    def heavy_cart_operations(self):
        """Simulate heavy cart operations"""
        for i in range(3):
            self.client.post("/add-to-cart", data={"book_id": str(i+1), "quantity": "2"})
            self.client.get("/cart")

class BurstyUser(HttpUser):
    """User class for simulating peak traffic"""
    tasks = [BurstyUserBehavior]
    wait_time = between(0.1, 1)  # Very short wait times
    weight = 1  # 10% of users will be bursty

# Performance Testing Functions (from test_performance.py)

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
        pr.print_stats(sort='cumulative')
        profiling_output = sys.stdout.getvalue()
        sys.stdout = old_stdout
        
        # Print profiling results
        print(profiling_output)
        
        return result
    except Exception as e:
        pr.disable()
        sys.stdout = old_stdout
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
        if 'payment' in func.__name__.lower():
            number_of_runs = 10  # Fewer runs for slower functions
        else:
            number_of_runs = 100  # More runs for faster functions
        
        # Create a wrapper function for timeit
        def wrapper():
            return func(*args, **kwargs)
        
        # Measure execution time
        total_time = timeit.timeit(wrapper, number=number_of_runs)
        average_time = total_time / number_of_runs
        
        print(f"Average time over {number_of_runs} runs: {average_time:.6f} seconds")
        print()
        
        return average_time
    except Exception as e:
        print(f"Error during timing: {e}")
        return None

# Performance Test Scenarios for Locust Integration

class PerformanceTestBehavior(TaskSet):
    """TaskSet that includes performance profiling of requests"""
    
    def on_start(self):
        """Initialize performance tracking"""
        self.request_times = []
        self.profile_data = {}
    
    @task(1)
    def profile_homepage_load(self):
        """Profile homepage loading performance"""
        def homepage_request():
            return self.client.get("/")
        
        # Time and profile the request
        start_time = time.time()
        response = homepage_request()
        end_time = time.time()
        
        request_time = end_time - start_time
        self.request_times.append(('homepage', request_time))
        
        if len(self.request_times) % 10 == 0:  # Print stats every 10 requests
            avg_time = sum(t[1] for t in self.request_times[-10:]) / 10
            print(f"Average homepage load time (last 10): {avg_time:.4f}s")
    
    @task(1) 
    def profile_cart_operations(self):
        """Profile cart operation performance"""
        def cart_operations():
            # Add to cart
            add_response = self.client.post("/add-to-cart", 
                                          data={"book_id": "1", "quantity": "1"})
            # View cart
            view_response = self.client.get("/cart")
            return add_response, view_response
        
        start_time = time.time()
        responses = cart_operations()
        end_time = time.time()
        
        request_time = end_time - start_time
        self.request_times.append(('cart_ops', request_time))
        
        if len(self.request_times) % 5 == 0:  # Print stats every 5 requests
            cart_times = [t[1] for t in self.request_times if t[0] == 'cart_ops'][-5:]
            if cart_times:
                avg_time = sum(cart_times) / len(cart_times)
                print(f"Average cart operations time (last 5): {avg_time:.4f}s")
    
    def on_stop(self):
        """Print performance summary when user stops"""
        if self.request_times:
            homepage_times = [t[1] for t in self.request_times if t[0] == 'homepage']
            cart_times = [t[1] for t in self.request_times if t[0] == 'cart_ops']
            
            print(f"\n=== Performance Summary for User ===")
            if homepage_times:
                print(f"Homepage requests: {len(homepage_times)}")
                print(f"Average homepage time: {sum(homepage_times)/len(homepage_times):.4f}s")
                print(f"Min homepage time: {min(homepage_times):.4f}s")
                print(f"Max homepage time: {max(homepage_times):.4f}s")
            
            if cart_times:
                print(f"Cart operation requests: {len(cart_times)}")
                print(f"Average cart ops time: {sum(cart_times)/len(cart_times):.4f}s")
                print(f"Min cart ops time: {min(cart_times):.4f}s")
                print(f"Max cart ops time: {max(cart_times):.4f}s")

class PerformanceUser(HttpUser):
    """User class focused on performance testing and profiling"""
    tasks = [PerformanceTestBehavior]
    wait_time = between(2, 5)
    weight = 1  # Small percentage for detailed performance analysis

# Standalone Performance Testing Functions

def run_standalone_performance_tests():
    """Run performance tests independently of Locust"""
    print("=== STANDALONE PERFORMANCE TESTING ===")
    
    # Import Flask app for direct testing
    try:
        from app import app
        
        with app.test_client() as client:
            print("Testing Flask application performance...")
            
            # Test homepage performance
            def test_homepage():
                return client.get('/')
            
            def test_add_to_cart():
                return client.post('/add-to-cart', data={'book_id': '1', 'quantity': '1'})
            
            def test_view_cart():
                return client.get('/cart')
            
            def test_search():
                return client.get('/search?query=python')
            
            # Run performance tests
            print("\n1. Homepage Performance:")
            time_function(test_homepage)
            
            print("2. Add to Cart Performance:")
            time_function(test_add_to_cart)
            
            print("3. View Cart Performance:")
            time_function(test_view_cart)
            
            print("4. Search Performance:")
            time_function(test_search)
            
            # Profile a complex operation
            print("5. Profiling Add to Cart Operation:")
            profile_function(test_add_to_cart)
            
    except ImportError as e:
        print(f"Could not import Flask app: {e}")
        print("Make sure app.py is in the same directory")

# Main execution for direct testing
if __name__ == "__main__":
    print("=== LOCUST LOAD TESTING WITH PERFORMANCE ANALYSIS ===")
    print("This file is configured for Locust load testing with integrated performance testing.")
    print("\nTo run load tests:")
    print("1. Start your Flask app: python app.py")
    print("2. Run Locust: locust -f locustfile.py --host=http://localhost:5000")
    print("3. Open browser: http://localhost:8089")
    print("\nUser Types:")
    print("- BookstoreUser (70%): General browsing behavior")
    print("- AuthenticatedUser (20%): Logged-in user behavior")  
    print("- BurstyUser (10%): Peak traffic simulation")
    print("- PerformanceUser (5%): Detailed performance profiling")
    print("\nLoad Test Scenarios:")
    print("- Homepage browsing")
    print("- Book searching and viewing")
    print("- Cart operations (add/view)")
    print("- User registration and login")
    print("- Checkout flow testing")
    print("- Performance profiling and timing")
    print("\n" + "=" * 50)
    
    # Ask user if they want to run standalone performance tests
    print("\nWould you like to run standalone performance tests? (y/n)")
    try:
        choice = input().lower().strip()
        if choice in ['y', 'yes', 'Y', 'YES', '']:
            run_standalone_performance_tests()
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping standalone performance tests...")
    
    print("=" * 50)