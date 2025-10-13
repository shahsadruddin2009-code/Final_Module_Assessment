#!/bin/bash
# Locust Load Testing Quick Start Script

echo "=== BOOKSTORE LOAD TESTING ==="
echo ""
echo "Make sure your Flask app is running first:"
echo "python app.py"
echo ""
echo "Starting Locust Web UI..."
echo "Open http://localhost:8089 in your browser"
echo ""

# Start Locust with the bookstore as the target
locust -f locustfile.py --host=http://localhost:5000