#!/usr/bin/env python3
"""
Test script to verify the project setup
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()

def check_directory_structure():
    """Check if all required directories and files exist"""
    print("🔍 Checking project structure...")
    
    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "backend/.env.example",
        "backend/routers/__init__.py",
        "backend/services/__init__.py",
        "backend/models/__init__.py",
        "backend/utils/__init__.py",
        "frontend/package.json",
        "frontend/src/app/page.tsx",
        "frontend/src/lib/api.ts",
        "README.md",
        "docker-compose.yml"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ All required files exist")
        return True

def check_backend_dependencies():
    """Check if backend dependencies can be imported"""
    print("\n🔍 Checking backend dependencies...")
    
    try:
        # Change to backend directory
        os.chdir("backend")
        
        # Try importing key dependencies
        import fastapi
        import uvicorn
        import motor
        import pydantic
        from passlib.context import CryptContext
        
        print("✅ Backend dependencies are available")
        return True
        
    except ImportError as e:
        print(f"❌ Missing backend dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking backend dependencies: {e}")
        return False
    finally:
        # Change back to root directory
        os.chdir("..")

def check_frontend_dependencies():
    """Check if frontend dependencies exist"""
    print("\n🔍 Checking frontend dependencies...")
    
    if not check_file_exists("frontend/node_modules"):
        print("❌ Frontend dependencies not installed. Run 'npm install' in frontend directory.")
        return False
    
    print("✅ Frontend dependencies are installed")
    return True

def main():
    """Main test function"""
    print("🚀 Cognix-AI Project Setup Verification\n")
    
    all_checks_passed = True
    
    # Check project structure
    if not check_directory_structure():
        all_checks_passed = False
    
    # Check backend dependencies (optional, might not be installed yet)
    try:
        if not check_backend_dependencies():
            print("ℹ️  Backend dependencies not installed. Run 'pip install -r requirements.txt' in backend directory.")
    except:
        print("ℹ️  Backend dependencies not installed. Run 'pip install -r requirements.txt' in backend directory.")
    
    # Check frontend dependencies (optional, might not be installed yet)
    if not check_frontend_dependencies():
        print("ℹ️  Frontend dependencies not installed. Run 'npm install' in frontend directory.")
    
    print("\n" + "="*50)
    
    if all_checks_passed:
        print("✅ Project setup verification completed successfully!")
        print("\nNext steps:")
        print("1. Install backend dependencies: cd backend && pip install -r requirements.txt")
        print("2. Install frontend dependencies: cd frontend && npm install")
        print("3. Set up environment variables by copying .env.example files")
        print("4. Start MongoDB (locally or use MongoDB Atlas)")
        print("5. Run the backend: cd backend && python main.py")
        print("6. Run the frontend: cd frontend && npm run dev")
    else:
        print("❌ Project setup verification failed!")
        print("Please check the missing files and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()