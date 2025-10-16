#!/usr/bin/env python3
"""
Simple load test script for the Flask bookstore application
Uses Flask's test client to simulate HTTP requests
"""

import time
import threading
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import app

def create_test_client():
    """Create a Flask test client"""
    app.config['TESTING'] = True
    return app.test_client()

def simulate_user_session(user_id, num_requests=10):
    """Simulate a user session with multiple requests"""
    client = create_test_client()
    results = []
    
    print(f"User {user_id} starting session...")
    
    for i in range(num_requests):
        start_time = time.time()
        
        # Simulate different user actions
        action = random.choice(['homepage', 'search', 'add_to_cart', 'view_cart'])
        
        try:
            if action == 'homepage':
                response = client.get('/')
            elif action == 'search':
                query = random.choice(['python', 'flask', 'programming', 'web'])
                response = client.get(f'/search?query={query}')
            elif action == 'add_to_cart':
                # Simulate adding a book to cart
                book_title = random.choice(['Python Programming', 'Flask Web Development', 'JavaScript Guide'])
                response = client.post('/add-to-cart', data={
                    'title': book_title,
                    'quantity': str(random.randint(1, 3))
                })
            elif action == 'view_cart':
                response = client.get('/cart')
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            results.append({
                'user_id': user_id,
                'action': action,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'success': response.status_code in [200, 302, 404]  # 404 is expected for some URLs
            })
            
            # Small delay between requests
            time.sleep(random.uniform(0.1, 0.5))
            
        except Exception as e:
            results.append({
                'user_id': user_id,
                'action': action,
                'status_code': 500,
                'response_time_ms': 0,
                'success': False,
                'error': str(e)
            })
    
    print(f"User {user_id} completed session")
    return results

def run_load_test(num_users=10, requests_per_user=10):
    """Run load test with specified number of users"""
    print(f" Starting load test with {num_users} users, {requests_per_user} requests per user")
    print("=" * 60)
    
    start_time = time.time()
    all_results = []
    
    # Use ThreadPoolExecutor to simulate concurrent users
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        # Submit all user sessions
        futures = [
            executor.submit(simulate_user_session, user_id, requests_per_user)
            for user_id in range(1, num_users + 1)
        ]
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                user_results = future.result()
                all_results.extend(user_results)
            except Exception as e:
                print(f"Error in user session: {e}")
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Analyze results
    print("\n Load Test Results")
    print("=" * 60)
    
    total_requests = len(all_results)
    successful_requests = sum(1 for r in all_results if r['success'])
    failed_requests = total_requests - successful_requests
    
    if total_requests > 0:
        success_rate = (successful_requests / total_requests) * 100
        avg_response_time = sum(r['response_time_ms'] for r in all_results) / total_requests
        max_response_time = max(r['response_time_ms'] for r in all_results)
        min_response_time = min(r['response_time_ms'] for r in all_results)
        
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {successful_requests}")
        print(f"Failed Requests: {failed_requests}")
        print(f"Success Rate: {success_rate:.2f}%")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Requests per Second: {total_requests/total_duration:.2f}")
        print(f"Average Response Time: {avg_response_time:.2f} ms")
        print(f"Min Response Time: {min_response_time:.2f} ms")
        print(f"Max Response Time: {max_response_time:.2f} ms")
        
        # Status code distribution
        status_codes = {}
        for result in all_results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        print("\nStatus Code Distribution:")
        for code, count in sorted(status_codes.items()):
            print(f"  {code}: {count} requests")
        
        # Action distribution
        actions = {}
        for result in all_results:
            action = result['action']
            actions[action] = actions.get(action, 0) + 1
        
        print("\nAction Distribution:")
        for action, count in sorted(actions.items()):
            avg_time = sum(r['response_time_ms'] for r in all_results if r['action'] == action) / count
            print(f"  {action}: {count} requests (avg: {avg_time:.2f} ms)")
    
    print("\n Load test completed!")
    return all_results

if __name__ == '__main__':
    # Run different load test scenarios
    print("Flask Bookstore Load Testing")
    print("=" * 40)
    
    # Scenario 1: Light load
    print("\n Scenario 1: Light Load (5 users, 5 requests each)")
    run_load_test(num_users=5, requests_per_user=5)
    
    time.sleep(2)  # Brief pause between scenarios
    
    # Scenario 2: Medium load
    print("\n Scenario 2: Medium Load (10 users, 10 requests each)")
    run_load_test(num_users=10, requests_per_user=10)
    
    time.sleep(2)  # Brief pause between scenarios
    
    # Scenario 3: Heavy load
    print("\n Scenario 3: Heavy Load (20 users, 15 requests each)")
    run_load_test(num_users=20, requests_per_user=15)