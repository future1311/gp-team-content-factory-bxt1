from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import asyncio
from dotenv import load_dotenv
from seedance_client import SeedanceAPIClient
# Import services extracted from Trae skills (runs standalone anywhere)
from services import AgentOrchestrator

# Load environment variables
load_dotenv()

# In-memory storage for tasks (replace with proper database in production)
tasks_db: Dict[str, Dict[str, Any]] = {}

# Import services extracted from Trae skills (runs standalone anywhere)
from services import AgentOrchestrator
from services.orchestrator import update_task_db_reference

# Initialize orchestrator and pass global tasks_db reference
# Fix circular import issue: pass tasks_db into orchestrator instead of importing from main
orchestrator = AgentOrchestrator()
# Gán tasks_db vào orchestrator để cập nhật trạng thái
update_task_db_reference(tasks_db)

app = FastAPI(title="Agent Orchestrator API", version="1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class VideoBrief(BaseModel):
    brief: str = Field(..., description="Product brief for video creation")
    product_images: Optional[List[str]] = Field(None, description="List of product image URLs")
    ratio: str = Field("9:16", description="Aspect ratio (9:16 for TikTok/Reels)")
    duration: int = Field(15, description="Video duration in seconds")
    generate_audio: bool = Field(True, description="Generate synchronized audio")

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    current_step: str
    video_url: Optional[str] = None
    error: Optional[str] = None
    social_video_generator_completed_output: Optional[Dict[str, Any]] = None
    seedance_video_director_completed_output: Optional[Dict[str, Any]] = None
    seedance2_camera_man_completed_output: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"

# Initialize Seedance client
def get_seedance_client():
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ARK_API_KEY not configured")
    return SeedanceAPIClient(api_key=api_key)

async def process_video_task(task_id: str, brief: VideoBrief):
    """Orchestrate the full video creation workflow: social-video-generator → seedance-video-director → seedance2-camera-man"""
    print(f"[DEBUG] Task {task_id}: Bắt đầu xử lý video")
    try:
        tasks_db[task_id].update({
            "status": "processing",
            "current_step": "agent_orchestrator",
            "message": "Đang điều phối toàn bộ quy trình tạo video..."
        })
        print(f"[DEBUG] Task {task_id}: Gọi orchestrator với brief đầy đủ")
        
        # Gọi orchestrator để xử lý toàn bộ luồng
        orchestrator_result = await orchestrator.process_video(brief.dict(), task_id)
        # Cập nhật trạng thái task với kết quả từ orchestrator
        tasks_db[task_id].update(orchestrator_result)
        print(f"[DEBUG] Task {task_id}: {orchestrator_result.get('message', 'Hoàn thành xử lý')}")

    except Exception as e:
        tasks_db[task_id].update({
            "status": "failed",
            "error": str(e),
            "message": f"Error: {str(e)}"
        })

@app.post("/api/create-video", response_model=TaskStatusResponse)
async def create_video(brief: VideoBrief, background_tasks: BackgroundTasks):
    """Start a new video creation task with full orchestration"""
    import uuid
    task_id = str(uuid.uuid4())
    
    tasks_db[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "current_step": "waiting",
        "brief": brief.dict(),
        "message": "Task queued, waiting to start..."
    }
    
    background_tasks.add_task(process_video_task, task_id, brief)
    
    return TaskStatusResponse(**tasks_db[task_id])

@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get status of a video creation task"""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusResponse(**tasks_db[task_id])

@app.get("/api/tasks")
async def list_tasks(limit: int = 10):
    """List all recent tasks"""
    return list(tasks_db.values())[-limit:]

@app.get("/")
async def root():
    return {
        "message": "Agent Orchestrator API is running",
        "docs": "/docs",
        "workflow": "social-video-generator → seedance-video-director → seedance2-camera-man"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
