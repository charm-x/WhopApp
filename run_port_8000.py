from app import app, init_db

if __name__ == '__main__':
    print("Starting Whop Gamify App on port 8000...")
    print("Initializing database...")
    init_db()
    print("Database initialized!")
    print("Starting web server...")
    print("App will be available at: http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        app.run(host='127.0.0.1', port=8000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
