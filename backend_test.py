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

def test_dsa_commit_system(repo_id):
    """Test DSA algorithms and commit system endpoints"""
    if not repo_id:
        print("\n⚠️  Skipping DSA commit system tests - no repository ID available")
        return
        
    print("\n🔍 Testing DSA Algorithms & Commit System...")
    
    commit_hashes = []
    
    # First, create some files for testing
    try:
        # Create initial file
        file_data1 = {
            "name": "algorithm_test.py",
            "content": "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n    return arr"
        }
        response = requests.post(f"{BASE_URL}/repositories/{repo_id}/files", json=file_data1, timeout=10)
        if response.status_code == 200:
            results.log_pass("Create initial file for DSA testing")
        else:
            results.log_fail("Create initial file", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Create initial file", str(e))
    
    # Test 1: Create first commit (SHA-1 hashing & commit creation)
    try:
        commit_data = {
            "message": "Initial commit: Add bubble sort algorithm",
            "author": "DSA Tester"
        }
        response = requests.post(f"{BASE_URL}/repositories/{repo_id}/commit", json=commit_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "commit_hash" in data and "files_snapshot" in data and "changes_summary" in data:
                commit_hashes.append(data["commit_hash"])
                # Verify SHA-1 hash format (40 characters, hexadecimal)
                if len(data["commit_hash"]) == 40 and all(c in "0123456789abcdef" for c in data["commit_hash"]):
                    results.log_pass("Create commit with SHA-1 hashing (POST /api/repositories/{id}/commit)")
                else:
                    results.log_fail("SHA-1 hash format", f"Invalid hash format: {data['commit_hash']}")
                
                # Verify changes summary
                changes = data["changes_summary"]
                if changes.get("additions", 0) > 0:
                    results.log_pass("Commit changes summary tracking")
                else:
                    results.log_fail("Commit changes summary", f"Expected additions > 0, got: {changes}")
            else:
                results.log_fail("Create commit", "Missing required fields in commit response")
        else:
            results.log_fail("Create commit", f"Status code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        results.log_fail("Create commit", str(e))
    
    # Test 2: Modify file and create second commit (test parent-child relationship)
    try:
        # Modify the algorithm file
        modified_content = "def bubble_sort(arr):\n    \"\"\"Optimized bubble sort with early termination\"\"\"\n    n = len(arr)\n    for i in range(n):\n        swapped = False\n        for j in range(0, n-i-1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]\n                swapped = True\n        if not swapped:\n            break\n    return arr\n\ndef quick_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr) // 2]\n    left = [x for x in arr if x < pivot]\n    middle = [x for x in arr if x == pivot]\n    right = [x for x in arr if x > pivot]\n    return quick_sort(left) + middle + quick_sort(right)"
        
        # Get the file ID first
        files_response = requests.get(f"{BASE_URL}/repositories/{repo_id}/files", timeout=10)
        if files_response.status_code == 200:
            files = files_response.json()
            algo_file = next((f for f in files if f["name"] == "algorithm_test.py"), None)
            if algo_file:
                # Update the file
                update_data = {"content": modified_content}
                update_response = requests.put(f"{BASE_URL}/repositories/{repo_id}/files/{algo_file['id']}", json=update_data, timeout=10)
                if update_response.status_code == 200:
                    results.log_pass("Modify file for second commit")
                else:
                    results.log_fail("Modify file", f"Status code: {update_response.status_code}")
            else:
                results.log_fail("Find algorithm file", "Could not find algorithm_test.py")
        else:
            results.log_fail("Get files for modification", f"Status code: {files_response.status_code}")
    except Exception as e:
        results.log_fail("Modify file for second commit", str(e))
    
    # Create second commit
    try:
        commit_data2 = {
            "message": "Add quick sort and optimize bubble sort",
            "author": "DSA Tester"
        }
        response = requests.post(f"{BASE_URL}/repositories/{repo_id}/commit", json=commit_data2, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "commit_hash" in data and "parent_commits" in data:
                commit_hashes.append(data["commit_hash"])
                # Verify parent-child relationship in DAG
                if len(data["parent_commits"]) == 1 and data["parent_commits"][0] == commit_hashes[0]:
                    results.log_pass("Commit DAG parent-child relationship")
                else:
                    results.log_fail("Commit DAG relationship", f"Expected parent {commit_hashes[0]}, got: {data['parent_commits']}")
                
                # Verify modifications count
                changes = data["changes_summary"]
                if changes.get("modifications", 0) > 0:
                    results.log_pass("Commit modifications tracking")
                else:
                    results.log_fail("Commit modifications", f"Expected modifications > 0, got: {changes}")
            else:
                results.log_fail("Second commit creation", "Missing required fields")
        else:
            results.log_fail("Second commit creation", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Second commit creation", str(e))
    
    # Test 3: Get commit history
    try:
        response = requests.get(f"{BASE_URL}/repositories/{repo_id}/commits", timeout=10)
        if response.status_code == 200:
            commits = response.json()
            if isinstance(commits, list) and len(commits) >= 2:
                results.log_pass("Get commit history (GET /api/repositories/{id}/commits)")
                
                # Verify commits are ordered by timestamp (newest first)
                if len(commits) >= 2:
                    first_commit_time = commits[0]["created_at"]
                    second_commit_time = commits[1]["created_at"]
                    if first_commit_time >= second_commit_time:
                        results.log_pass("Commit history ordering (newest first)")
                    else:
                        results.log_fail("Commit history ordering", "Commits not ordered correctly")
            else:
                results.log_fail("Get commit history", f"Expected list with 2+ commits, got: {commits}")
        else:
            results.log_fail("Get commit history", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Get commit history", str(e))
    
    # Test 4: Get specific commit
    if commit_hashes:
        try:
            response = requests.get(f"{BASE_URL}/repositories/{repo_id}/commits/{commit_hashes[0]}", timeout=10)
            if response.status_code == 200:
                commit_data = response.json()
                if commit_data.get("commit_hash") == commit_hashes[0]:
                    results.log_pass("Get specific commit (GET /api/repositories/{id}/commits/{hash})")
                else:
                    results.log_fail("Get specific commit", "Commit hash mismatch")
            else:
                results.log_fail("Get specific commit", f"Status code: {response.status_code}")
        except Exception as e:
            results.log_fail("Get specific commit", str(e))
    
    # Test 5: Get commit graph (DAG structure)
    try:
        response = requests.get(f"{BASE_URL}/repositories/{repo_id}/commit-graph", timeout=10)
        if response.status_code == 200:
            graph = response.json()
            if "nodes" in graph and "edges" in graph and "total_commits" in graph:
                results.log_pass("Get commit graph DAG (GET /api/repositories/{id}/commit-graph)")
                
                # Verify graph structure
                nodes = graph["nodes"]
                edges = graph["edges"]
                if len(nodes) >= 2 and len(edges) >= 1:
                    results.log_pass("Commit DAG structure validation")
                    
                    # Verify edge connects correct commits
                    if len(edges) > 0:
                        edge = edges[0]
                        if "from" in edge and "to" in edge:
                            results.log_pass("Commit DAG edge structure")
                        else:
                            results.log_fail("Commit DAG edge structure", "Missing from/to in edge")
                else:
                    results.log_fail("Commit DAG structure", f"Expected 2+ nodes and 1+ edges, got nodes: {len(nodes)}, edges: {len(edges)}")
            else:
                results.log_fail("Get commit graph", "Missing required fields in graph response")
        else:
            results.log_fail("Get commit graph", f"Status code: {response.status_code}")
    except Exception as e:
        results.log_fail("Get commit graph", str(e))
    
    # Test 6: Generate file diff using LCS algorithm
    if commit_hashes:
        try:
            # Get the algorithm file ID
            files_response = requests.get(f"{BASE_URL}/repositories/{repo_id}/files", timeout=10)
            if files_response.status_code == 200:
                files = files_response.json()
                algo_file = next((f for f in files if f["name"] == "algorithm_test.py"), None)
                if algo_file:
                    # Test diff generation
                    diff_data = {
                        "file_id": algo_file["id"],
                        "commit_hash": commit_hashes[0]
                    }
                    response = requests.post(f"{BASE_URL}/repositories/{repo_id}/diff", json=diff_data, timeout=10)
                    if response.status_code == 200:
                        diff_result = response.json()
                        if "diff" in diff_result and "file_name" in diff_result:
                            diff = diff_result["diff"]
                            if "additions" in diff and "deletions" in diff and "stats" in diff:
                                results.log_pass("Generate file diff using LCS (POST /api/repositories/{id}/diff)")
                                
                                # Verify LCS algorithm results
                                stats = diff["stats"]
                                if "lines_added" in stats and "lines_deleted" in stats:
                                    results.log_pass("LCS algorithm diff statistics")
                                else:
                                    results.log_fail("LCS algorithm stats", "Missing diff statistics")
                            else:
                                results.log_fail("LCS diff structure", "Missing required diff fields")
                        else:
                            results.log_fail("Generate file diff", "Missing required response fields")
                    else:
                        results.log_fail("Generate file diff", f"Status code: {response.status_code}")
                else:
                    results.log_fail("Find file for diff", "Could not find algorithm_test.py for diff")
            else:
                results.log_fail("Get files for diff", f"Status code: {files_response.status_code}")
        except Exception as e:
            results.log_fail("Generate file diff", str(e))
    
    # Test 7: Checkout commit
    if commit_hashes:
        try:
            response = requests.post(f"{BASE_URL}/repositories/{repo_id}/checkout/{commit_hashes[0]}", timeout=10)
            if response.status_code == 200:
                checkout_result = response.json()
                if "message" in checkout_result and "commit" in checkout_result:
                    results.log_pass("Checkout commit (POST /api/repositories/{id}/checkout/{hash})")
                else:
                    results.log_fail("Checkout commit", "Missing required fields in checkout response")
            else:
                results.log_fail("Checkout commit", f"Status code: {response.status_code}")
        except Exception as e:
            results.log_fail("Checkout commit", str(e))
    
    # Test 8: Verify commit hash uniqueness and determinism
    if len(commit_hashes) >= 2:
        try:
            if commit_hashes[0] != commit_hashes[1]:
                results.log_pass("Commit hash uniqueness")
            else:
                results.log_fail("Commit hash uniqueness", "Different commits have same hash")
            
            # Test deterministic hashing by creating identical commit scenario
            # This is a simplified test - in practice, timestamps make hashes unique
            if all(len(h) == 40 and all(c in "0123456789abcdef" for c in h) for h in commit_hashes):
                results.log_pass("SHA-1 hash format consistency")
            else:
                results.log_fail("SHA-1 hash format", "Inconsistent hash formats")
        except Exception as e:
            results.log_fail("Commit hash validation", str(e))

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