#!/usr/bin/env python3
"""
Main entry point for the Debugging Agents Research Platform
Starts both the backend API server and serves the frontend
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        # 'flask', 'flask-cors', 'pandas', 'numpy', 
        # 'matplotlib', 'seaborn', 'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting backend server...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Start Flask app
    try:
        from app import app
        app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return False

def start_frontend():
    """Start a simple HTTP server for the frontend"""
    print("🌐 Starting frontend server...")
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent / "frontend"
    os.chdir(frontend_dir)
    
    try:
        # Use Python's built-in HTTP server
        import http.server
        import socketserver
        
        PORT = 8080
        Handler = http.server.SimpleHTTPRequestHandler
        
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"Frontend server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return False

def open_browser():
    """Open the web browser to the application"""
    time.sleep(3)  # Wait for servers to start
    try:
        webbrowser.open('http://localhost:8080')
        print("🌐 Opening web browser...")
    except Exception as e:
        print(f"⚠️ Could not open browser: {e}")
        print("🌐 Please open http://localhost:8080 in your browser")

def main():
    """Main function to start the application"""
    print("=" * 60)
    print("🤖 Debugging Agents Research Platform")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        return 1
    
    print("✅ All dependencies found")
    
    # Create necessary directories
    data_dir = Path(__file__).parent / "data"
    reports_dir = Path(__file__).parent / "reports"
    processed_dir = data_dir / "processed"
    
    for directory in [data_dir, reports_dir, processed_dir]:
        directory.mkdir(exist_ok=True)
    
    print("📁 Directories created")
    
    # Copy data files to the correct location
    try:
        import shutil
        
        # Copy CSV files to data directory
        source_files = [
            "debugging_agents_synthetic_annotations.csv",
            "synthetic_pdf_papers_dataset.csv"
        ]
        
        for file in source_files:
            source_path = Path(__file__).parent / file
            dest_path = data_dir / file
            
            if source_path.exists() and not dest_path.exists():
                shutil.copy2(source_path, dest_path)
                print(f"📄 Copied {file} to data directory")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not copy data files: {e}")
    
    print("\n🚀 Starting servers...")
    print("📊 Backend API: http://localhost:5000")
    print("🌐 Frontend UI: http://localhost:8080")
    print("\nPress Ctrl+C to stop all servers")
    print("=" * 60)
    
    try:
        # Start backend in a separate thread
        backend_thread = threading.Thread(target=start_backend, daemon=True)
        backend_thread.start()
        
        # Start browser opener in a separate thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start frontend (this will block)
        start_frontend()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down servers...")
        print("✅ Application stopped")
        return 0
    except Exception as e:
        print(f"\n❌ Error running application: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
