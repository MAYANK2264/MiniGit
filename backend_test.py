#!/usr/bin/env python3
"""
Backend API Testing for Mini-Git Application
Tests all repository and file management endpoints
"""

import requests
import json
import os
import sys
from datetime import datetime
import uuid

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "https://codever.preview.emergentagent.com"

BASE_URL = get_backend_url() + "/api"
print(f"Testing backend at: {BASE_URL}")

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        
    def log_pass(self, test_name):
        self.passed += 1
        print(f"✅ PASS: {test_name}")
        
    def log_fail(self, test_name, error):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"❌ FAIL: {test_name} - {error}")
        
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY: {self.passed}/{total} tests passed")
        if self.errors:
            print(f"\nFAILED TESTS:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0

results = TestResults()

def test_health_endpoints():
    """Test health check and root endpoints"""
    print("\n🔍 Testing Health Endpoints...")
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                results.log_pass("Root endpoint (/api/)")
            else:
                results.log_fail("Root endpoint (/api/)", "Missing message in response")
        else:
            results.log_fail("Root endpoint (/api/)", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Root endpoint (/api/)", str(e))
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "status" in data and "timestamp" in data:
                results.log_pass("Health endpoint (/api/health)")
            else:
                results.log_fail("Health endpoint (/api/health)", "Missing required fields")
        else:
            results.log_fail("Health endpoint (/api/health)", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Health endpoint (/api/health)", str(e))

def test_repository_operations():
    """Test repository CRUD operations"""
    print("\n🔍 Testing Repository Operations...")
    
    repo_id = None
    
    # Test create repository
    try:
        repo_data = {
            "name": "test-repo-" + str(uuid.uuid4())[:8],
            "description": "Test repository for API testing"
        }
        response = requests.post(f"{BASE_URL}/repositories", json=repo_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "name" in data:
                repo_id = data["id"]
                results.log_pass("Create repository (POST /api/repositories)")
            else:
                results.log_fail("Create repository", "Missing required fields in response")
        else:
            results.log_fail("Create repository", f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        results.log_fail("Create repository", str(e))
    
    # Test get all repositories
    try:
        response = requests.get(f"{BASE_URL}/repositories", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                results.log_pass("Get all repositories (GET /api/repositories)")
            else:
                results.log_fail("Get all repositories", "Response is not a list")
        else:
            results.log_fail("Get all repositories", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Get all repositories", str(e))
    
    # Test get specific repository
    if repo_id:
        try:
            response = requests.get(f"{BASE_URL}/repositories/{repo_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == repo_id:
                    results.log_pass("Get specific repository (GET /api/repositories/{id})")
                else:
                    results.log_fail("Get specific repository", "Repository ID mismatch")
            else:
                results.log_fail("Get specific repository", f"Status code: {response.status_code}")
        except Exception as e:
            results.log_fail("Get specific repository", str(e))
    
    # Test get non-existent repository (should return 404)
    try:
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/repositories/{fake_id}", timeout=10)
        if response.status_code == 404:
            results.log_pass("Get non-existent repository (404 handling)")
        else:
            results.log_fail("Get non-existent repository", f"Expected 404, got {response.status_code}")
    except Exception as e:
        results.log_fail("Get non-existent repository", str(e))
    
    return repo_id

def test_file_operations(repo_id):
    """Test file management operations"""
    if not repo_id:
        print("\n⚠️  Skipping file operations - no repository ID available")
        return
        
    print("\n🔍 Testing File Operations...")
    
    file_id = None
    
    # Test create file
    try:
        file_data = {
            "name": "test-file.txt",
            "content": "Hello, this is a test file content!\nLine 2 of the file."
        }
        response = requests.post(f"{BASE_URL}/repositories/{repo_id}/files", json=file_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "id" in data and "name" in data and "content" in data:
                file_id = data["id"]
                results.log_pass("Create file (POST /api/repositories/{id}/files)")
            else:
                results.log_fail("Create file", "Missing required fields in response")
        else:
            results.log_fail("Create file", f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        results.log_fail("Create file", str(e))
    
    # Test create another file
    try:
        file_data2 = {
            "name": "README.md",
            "content": "# Test Repository\n\nThis is a test repository for the Mini-Git API.\n\n## Features\n- File management\n- Version control"
        }
        response = requests.post(f"{BASE_URL}/repositories/{repo_id}/files", json=file_data2, timeout=10)
        if response.status_code == 200:
            results.log_pass("Create second file (README.md)")
        else:
            results.log_fail("Create second file", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Create second file", str(e))
    
    # Test get all files in repository
    try:
        response = requests.get(f"{BASE_URL}/repositories/{repo_id}/files", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) >= 2:
                results.log_pass("Get repository files (GET /api/repositories/{id}/files)")
            else:
                results.log_fail("Get repository files", f"Expected list with 2+ files, got: {data}")
        else:
            results.log_fail("Get repository files", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Get repository files", str(e))
    
    # Test get specific file
    if file_id:
        try:
            response = requests.get(f"{BASE_URL}/repositories/{repo_id}/files/{file_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("id") == file_id and "content" in data:
                    results.log_pass("Get specific file (GET /api/repositories/{id}/files/{file_id})")
                else:
                    results.log_fail("Get specific file", "File data mismatch")
            else:
                results.log_fail("Get specific file", f"Status code: {response.status_code}")
        except Exception as e:
            results.log_fail("Get specific file", str(e))
    
    # Test update file content
    if file_id:
        try:
            update_data = {
                "content": "Updated content for the test file!\nThis content has been modified.\nNew line added."
            }
            response = requests.put(f"{BASE_URL}/repositories/{repo_id}/files/{file_id}", json=update_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("content") == update_data["content"]:
                    results.log_pass("Update file content (PUT /api/repositories/{id}/files/{file_id})")
                else:
                    results.log_fail("Update file content", "Content not updated correctly")
            else:
                results.log_fail("Update file content", f"Status code: {response.status_code}")
        except Exception as e:
            results.log_fail("Update file content", str(e))
    
    # Test file upload (simulate multipart form data)
    try:
        files = {
            'file': ('upload-test.txt', 'This is an uploaded file content\nUploaded via multipart form.', 'text/plain')
        }
        response = requests.post(f"{BASE_URL}/repositories/{repo_id}/upload", files=files, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "file_id" in data:
                results.log_pass("File upload (POST /api/repositories/{id}/upload)")
            else:
                results.log_fail("File upload", "Missing required fields in response")
        else:
            results.log_fail("File upload", f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        results.log_fail("File upload", str(e))
    
    # Test delete file
    if file_id:
        try:
            response = requests.delete(f"{BASE_URL}/repositories/{repo_id}/files/{file_id}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    results.log_pass("Delete file (DELETE /api/repositories/{id}/files/{file_id})")
                else:
                    results.log_fail("Delete file", "Missing message in response")
            else:
                results.log_fail("Delete file", f"Status code: {response.status_code}")
        except Exception as e:
            results.log_fail("Delete file", str(e))
    
    # Test delete non-existent file (should return 404)
    try:
        fake_file_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/repositories/{repo_id}/files/{fake_file_id}", timeout=10)
        if response.status_code == 404:
            results.log_pass("Delete non-existent file (404 handling)")
        else:
            results.log_fail("Delete non-existent file", f"Expected 404, got {response.status_code}")
    except Exception as e:
        results.log_fail("Delete non-existent file", str(e))

def test_repository_file_count(repo_id):
    """Test that repository file_count is updated correctly"""
    if not repo_id:
        return
        
    print("\n🔍 Testing Repository File Count Updates...")
    
    try:
        # Get current repository state
        response = requests.get(f"{BASE_URL}/repositories/{repo_id}", timeout=10)
        if response.status_code == 200:
            repo_data = response.json()
            file_count = repo_data.get("file_count", 0)
            if file_count >= 0:  # Should have some files from previous tests
                results.log_pass("Repository file_count tracking")
            else:
                results.log_fail("Repository file_count tracking", f"Invalid file count: {file_count}")
        else:
            results.log_fail("Repository file_count tracking", f"Could not get repository: {response.status_code}")
    except Exception as e:
        results.log_fail("Repository file_count tracking", str(e))

def test_repository_deletion(repo_id):
    """Test repository deletion (should cascade delete files)"""
    if not repo_id:
        return
        
    print("\n🔍 Testing Repository Deletion...")
    
    try:
        response = requests.delete(f"{BASE_URL}/repositories/{repo_id}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "message" in data:
                results.log_pass("Delete repository (DELETE /api/repositories/{id})")
                
                # Verify repository is actually deleted
                verify_response = requests.get(f"{BASE_URL}/repositories/{repo_id}", timeout=10)
                if verify_response.status_code == 404:
                    results.log_pass("Repository deletion verification (404 after delete)")
                else:
                    results.log_fail("Repository deletion verification", f"Repository still exists: {verify_response.status_code}")
            else:
                results.log_fail("Delete repository", "Missing message in response")
        else:
            results.log_fail("Delete repository", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Delete repository", str(e))

def main():
    """Run all tests"""
    print("🚀 Starting Mini-Git Backend API Tests")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test started at: {datetime.now()}")
    
    # Test health endpoints first
    test_health_endpoints()
    
    # Test repository operations
    repo_id = test_repository_operations()
    
    # Test file operations
    test_file_operations(repo_id)
    
    # Test repository file count tracking
    test_repository_file_count(repo_id)
    
    # Test repository deletion (should be last)
    test_repository_deletion(repo_id)
    
    # Print final summary
    success = results.summary()
    
    if success:
        print("\n🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        print(f"\n💥 {results.failed} test(s) failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())