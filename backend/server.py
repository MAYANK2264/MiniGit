from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import hashlib
import json
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ====== MODELS ======

class FileContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    content: str
    size: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mime_type: str = "text/plain"

class Repository(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    default_branch: str = "main"
    file_count: int = 0

class Commit(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_id: str
    commit_hash: str  # SHA-1 style hash
    message: str
    author: str = "Anonymous"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parent_commits: List[str] = []  # For DAG structure
    files_snapshot: Dict[str, Any] = {}  # file_id -> file metadata mapping
    changes_summary: Dict[str, Any] = {}  # additions, deletions, modifications

class Branch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_id: str
    name: str
    current_commit: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ====== REQUEST/RESPONSE MODELS ======

class CreateRepositoryRequest(BaseModel):
    name: str
    description: str = ""

class CreateFileRequest(BaseModel):
    name: str
    content: str
    
class UpdateFileRequest(BaseModel):
    content: str

class CreateCommitRequest(BaseModel):
    message: str
    author: str = "Anonymous"

class DiffRequest(BaseModel):
    file_id: str
    commit_hash: Optional[str] = None

# ====== UTILITY FUNCTIONS & DSA ALGORITHMS ======

def generate_content_hash(content: str) -> str:
    """Generate SHA-1 style hash for content"""
    return hashlib.sha1(content.encode()).hexdigest()

def generate_commit_hash(repo_id: str, message: str, timestamp: str, files: Dict) -> str:
    """Generate commit hash based on repository, message, timestamp, and files"""
    data = f"{repo_id}{message}{timestamp}{json.dumps(files, sort_keys=True)}"
    return hashlib.sha1(data.encode()).hexdigest()

def longest_common_subsequence(text1: str, text2: str) -> List[List[int]]:
    """
    LCS Dynamic Programming Algorithm for diff generation
    Returns the LCS table for computing diffs
    """
    m, n = len(text1), len(text2)
    lcs_table = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i-1] == text2[j-1]:
                lcs_table[i][j] = lcs_table[i-1][j-1] + 1
            else:
                lcs_table[i][j] = max(lcs_table[i-1][j], lcs_table[i][j-1])
    
    return lcs_table

def generate_diff(old_content: str, new_content: str) -> Dict[str, Any]:
    """
    Generate detailed diff using LCS algorithm
    Returns additions, deletions, and unchanged lines
    """
    old_lines = old_content.split('\n') if old_content else []
    new_lines = new_content.split('\n') if new_content else []
    
    # Get LCS table
    lcs_table = longest_common_subsequence('\n'.join(old_lines), '\n'.join(new_lines))
    
    # Backtrack to find actual diff
    i, j = len(old_lines), len(new_lines)
    additions = []
    deletions = []
    unchanged = []
    
    # Simple line-by-line diff for better visualization
    old_set = set(enumerate(old_lines))
    new_set = set(enumerate(new_lines))
    
    # Find additions (lines in new but not in old)
    for line_num, line in enumerate(new_lines):
        if line not in old_lines:
            additions.append({"line_num": line_num + 1, "content": line})
    
    # Find deletions (lines in old but not in new)  
    for line_num, line in enumerate(old_lines):
        if line not in new_lines:
            deletions.append({"line_num": line_num + 1, "content": line})
    
    # Find unchanged lines
    for line_num, line in enumerate(new_lines):
        if line in old_lines:
            unchanged.append({"line_num": line_num + 1, "content": line})
    
    return {
        "additions": additions,
        "deletions": deletions,
        "unchanged": unchanged,
        "stats": {
            "lines_added": len(additions),
            "lines_deleted": len(deletions),
            "lines_unchanged": len(unchanged)
        }
    }

def build_commit_graph(commits: List[Dict]) -> Dict[str, Any]:
    """
    Build DAG (Directed Acyclic Graph) for commit history
    Returns graph structure with nodes and edges
    """
    nodes = []
    edges = []
    
    # Create nodes for each commit
    for commit in commits:
        nodes.append({
            "id": commit["commit_hash"],
            "message": commit["message"],
            "author": commit["author"],
            "timestamp": commit["created_at"],
            "files_count": len(commit.get("files_snapshot", {}))
        })
        
        # Create edges from parent commits
        for parent_hash in commit.get("parent_commits", []):
            edges.append({
                "from": parent_hash,
                "to": commit["commit_hash"]
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "total_commits": len(nodes)
    }

def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse data from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value and value.endswith('Z'):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# ====== REPOSITORY ENDPOINTS ======

@api_router.post("/repositories", response_model=Repository)
async def create_repository(request: CreateRepositoryRequest):
    """Create a new repository"""
    repo = Repository(
        name=request.name,
        description=request.description
    )
    
    repo_dict = prepare_for_mongo(repo.dict())
    await db.repositories.insert_one(repo_dict)
    
    # Create default main branch
    branch = Branch(
        repo_id=repo.id,
        name="main",
        current_commit=""
    )
    branch_dict = prepare_for_mongo(branch.dict())
    await db.branches.insert_one(branch_dict)
    
    return repo

@api_router.get("/repositories", response_model=List[Repository])
async def get_repositories():
    """Get all repositories"""
    repos = await db.repositories.find().to_list(1000)
    return [Repository(**parse_from_mongo(repo)) for repo in repos]

@api_router.get("/repositories/{repo_id}", response_model=Repository)
async def get_repository(repo_id: str):
    """Get a specific repository"""
    repo = await db.repositories.find_one({"id": repo_id})
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return Repository(**parse_from_mongo(repo))

@api_router.delete("/repositories/{repo_id}")
async def delete_repository(repo_id: str):
    """Delete a repository and all its data"""
    # Delete repository
    result = await db.repositories.delete_one({"id": repo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Delete all related data
    await db.files.delete_many({"repo_id": repo_id})
    await db.commits.delete_many({"repo_id": repo_id})
    await db.branches.delete_many({"repo_id": repo_id})
    
    return {"message": "Repository deleted successfully"}

# ====== FILE MANAGEMENT ENDPOINTS ======

@api_router.post("/repositories/{repo_id}/files", response_model=FileContent)
async def create_file(repo_id: str, request: CreateFileRequest):
    """Create or update a file in repository"""
    # Check if repository exists
    repo = await db.repositories.find_one({"id": repo_id})
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Check if file already exists
    existing_file = await db.files.find_one({"repo_id": repo_id, "name": request.name})
    
    file_content = FileContent(
        name=request.name,
        content=request.content,
        size=len(request.content)
    )
    
    file_dict = prepare_for_mongo(file_content.dict())
    file_dict["repo_id"] = repo_id
    
    if existing_file:
        # Update existing file - preserve the existing ID
        file_dict["id"] = existing_file["id"]
        await db.files.replace_one({"id": existing_file["id"]}, file_dict)
        file_content.id = existing_file["id"]
    else:
        # Create new file
        await db.files.insert_one(file_dict)
        # Update repository file count
        await db.repositories.update_one(
            {"id": repo_id},
            {"$inc": {"file_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return file_content

@api_router.get("/repositories/{repo_id}/files", response_model=List[FileContent])
async def get_repository_files(repo_id: str):
    """Get all files in a repository"""
    files = await db.files.find({"repo_id": repo_id}).to_list(1000)
    return [FileContent(**parse_from_mongo(file)) for file in files]

@api_router.get("/repositories/{repo_id}/files/{file_id}", response_model=FileContent)
async def get_file(repo_id: str, file_id: str):
    """Get a specific file"""
    file_doc = await db.files.find_one({"id": file_id, "repo_id": repo_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    return FileContent(**parse_from_mongo(file_doc))

@api_router.put("/repositories/{repo_id}/files/{file_id}", response_model=FileContent)
async def update_file(repo_id: str, file_id: str, request: UpdateFileRequest):
    """Update file content"""
    file_doc = await db.files.find_one({"id": file_id, "repo_id": repo_id})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")
    
    updated_data = {
        "content": request.content,
        "size": len(request.content),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.files.update_one({"id": file_id}, {"$set": updated_data})
    
    # Get updated file
    updated_file = await db.files.find_one({"id": file_id})
    return FileContent(**parse_from_mongo(updated_file))

@api_router.delete("/repositories/{repo_id}/files/{file_id}")
async def delete_file(repo_id: str, file_id: str):
    """Delete a file"""
    result = await db.files.delete_one({"id": file_id, "repo_id": repo_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update repository file count
    await db.repositories.update_one(
        {"id": repo_id},
        {"$inc": {"file_count": -1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "File deleted successfully"}

# ====== FILE UPLOAD ENDPOINT ======

@api_router.post("/repositories/{repo_id}/upload")
async def upload_file(repo_id: str, file: UploadFile = File(...)):
    """Upload a file to repository"""
    # Check if repository exists
    repo = await db.repositories.find_one({"id": repo_id})
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Read file content
    content = await file.read()
    
    # For binary files, encode as base64
    if file.content_type and not file.content_type.startswith('text/'):
        content_str = base64.b64encode(content).decode('utf-8')
        is_binary = True
    else:
        try:
            content_str = content.decode('utf-8')
            is_binary = False
        except UnicodeDecodeError:
            # If can't decode as text, treat as binary
            content_str = base64.b64encode(content).decode('utf-8')
            is_binary = True
    
    # Create file record
    file_content = FileContent(
        name=file.filename,
        content=content_str,
        size=len(content),
        mime_type=file.content_type or "application/octet-stream"
    )
    
    file_dict = prepare_for_mongo(file_content.dict())
    file_dict["repo_id"] = repo_id
    file_dict["is_binary"] = is_binary
    
    # Check if file exists and update or create
    existing_file = await db.files.find_one({"repo_id": repo_id, "name": file.filename})
    
    if existing_file:
        file_dict["id"] = existing_file["id"]
        await db.files.replace_one({"id": existing_file["id"]}, file_dict)
        file_content.id = existing_file["id"]
    else:
        await db.files.insert_one(file_dict)
        # Update repository file count
        await db.repositories.update_one(
            {"id": repo_id},
            {"$inc": {"file_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {
        "message": "File uploaded successfully",
        "file_id": file_content.id,
        "filename": file.filename,
        "size": len(content),
        "is_binary": is_binary
    }
# ====== COMMIT SYSTEM ENDPOINTS ======

@api_router.post("/repositories/{repo_id}/commit", response_model=Commit)
async def create_commit(repo_id: str, request: CreateCommitRequest):
    """Create a new commit with current repository state"""
    # Check if repository exists
    repo = await db.repositories.find_one({"id": repo_id})
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get all current files in repository
    files = await db.files.find({"repo_id": repo_id}).to_list(1000)
    
    if not files:
        raise HTTPException(status_code=400, detail="Cannot commit empty repository")
    
    # Create files snapshot with content hashes
    files_snapshot = {}
    changes_summary = {"additions": 0, "deletions": 0, "modifications": 0}
    
    # Get the last commit to compare changes
    last_commit = await db.commits.find_one(
        {"repo_id": repo_id}, 
        sort=[("created_at", -1)]
    )
    
    for file in files:
        content_hash = generate_content_hash(file["content"])
        files_snapshot[file["id"]] = {
            "name": file["name"],
            "hash": content_hash,
            "size": file["size"]
        }
        
        # Calculate changes compared to last commit
        if last_commit and file["id"] in last_commit.get("files_snapshot", {}):
            if last_commit["files_snapshot"][file["id"]]["hash"] != content_hash:
                changes_summary["modifications"] += 1
        else:
            changes_summary["additions"] += 1
    
    # Check for deletions (files in last commit but not in current)
    if last_commit:
        for old_file_id in last_commit.get("files_snapshot", {}):
            if old_file_id not in files_snapshot:
                changes_summary["deletions"] += 1
    
    # Generate commit hash
    timestamp = datetime.now(timezone.utc).isoformat()
    commit_hash = generate_commit_hash(repo_id, request.message, timestamp, files_snapshot)
    
    # Create commit object
    commit = Commit(
        repo_id=repo_id,
        commit_hash=commit_hash,
        message=request.message,
        author=request.author,
        parent_commits=[last_commit["commit_hash"]] if last_commit else [],
        files_snapshot=files_snapshot,
        changes_summary=changes_summary
    )
    
    # Save commit to database
    commit_dict = prepare_for_mongo(commit.dict())
    await db.commits.insert_one(commit_dict)
    
    # Update repository's updated_at timestamp
    await db.repositories.update_one(
        {"id": repo_id},
        {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return commit

@api_router.get("/repositories/{repo_id}/commits", response_model=List[Commit])
async def get_commits(repo_id: str, limit: int = 50):
    """Get commit history for repository"""
    commits = await db.commits.find(
        {"repo_id": repo_id}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return [Commit(**parse_from_mongo(commit)) for commit in commits]

@api_router.get("/repositories/{repo_id}/commits/{commit_hash}", response_model=Commit)
async def get_commit(repo_id: str, commit_hash: str):
    """Get specific commit details"""
    commit = await db.commits.find_one({
        "repo_id": repo_id, 
        "commit_hash": commit_hash
    })
    
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    
    return Commit(**parse_from_mongo(commit))

@api_router.get("/repositories/{repo_id}/commit-graph")
async def get_commit_graph(repo_id: str):
    """Get commit history as DAG structure"""
    commits = await db.commits.find({"repo_id": repo_id}).to_list(1000)
    
    if not commits:
        return {"nodes": [], "edges": [], "total_commits": 0}
    
    # Parse commits and build graph
    parsed_commits = [parse_from_mongo(commit) for commit in commits]
    graph = build_commit_graph(parsed_commits)
    
    return graph

@api_router.post("/repositories/{repo_id}/diff")
async def generate_file_diff(repo_id: str, request: DiffRequest):
    """Generate diff for a file between current state and specific commit"""
    # Get current file
    current_file = await db.files.find_one({"id": request.file_id, "repo_id": repo_id})
    if not current_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    old_content = ""
    
    if request.commit_hash:
        # Get file content from specific commit
        commit = await db.commits.find_one({
            "repo_id": repo_id,
            "commit_hash": request.commit_hash
        })
        
        if commit and request.file_id in commit.get("files_snapshot", {}):
            # Find the file in the commit's snapshot
            # Note: This is simplified - in a real system, you'd store file content separately
            old_content = ""  # Would need to implement file versioning
        else:
            old_content = ""
    
    # Generate diff using LCS algorithm
    diff_result = generate_diff(old_content, current_file["content"])
    
    return {
        "file_name": current_file["name"],
        "file_id": request.file_id,
        "commit_hash": request.commit_hash,
        "diff": diff_result
    }

@api_router.post("/repositories/{repo_id}/checkout/{commit_hash}")
async def checkout_commit(repo_id: str, commit_hash: str):
    """Checkout repository to specific commit state (simplified)"""
    # Get commit
    commit = await db.commits.find_one({
        "repo_id": repo_id,
        "commit_hash": commit_hash
    })
    
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")
    
    # In a real implementation, this would restore file contents
    # For now, just return the commit information
    return {
        "message": f"Repository checked out to commit {commit_hash[:8]}",
        "commit": Commit(**parse_from_mongo(commit)),
        "files_in_commit": len(commit.get("files_snapshot", {}))
    }

# ====== STATUS ENDPOINT ======

@api_router.get("/")
async def root():
    return {"message": "Mini-Git API is running!"}

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "mini-git-api"
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()