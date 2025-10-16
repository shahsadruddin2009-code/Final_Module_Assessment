from app import app
import threading
import time

def run_flask():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    print(" Starting Flask server...")
    
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    print(" Flask server started successfully!")
    print(" Access your app at: http://localhost:5000")
    print(" Press Ctrl+C to stop the server")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Shutting down Flask server...")