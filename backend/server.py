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
    files_snapshot: Dict[str, str] = {}  # file_id -> content_hash mapping
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

# ====== UTILITY FUNCTIONS ======

def generate_content_hash(content: str) -> str:
    """Generate SHA-1 style hash for content"""
    return hashlib.sha1(content.encode()).hexdigest()

def generate_commit_hash(repo_id: str, message: str, timestamp: str, files: Dict) -> str:
    """Generate commit hash based on repository, message, timestamp, and files"""
    data = f"{repo_id}{message}{timestamp}{json.dumps(files, sort_keys=True)}"
    return hashlib.sha1(data.encode()).hexdigest()

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
        content_str = content.decode('utf-8')
        is_binary = False
    
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
        await db.files.replace_one({"id": existing_file["id"]}, file_dict)
        file_content.id = existing_file["id"]
    else:
        await db.files.insert_one(file_dict)
        # Update repository file count
        await db.repositories.update_one(
            {"id": repo_id},
            {"$inc": {"file_count": 1}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": "File uploaded successfully", "file_id": file_content.id}

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