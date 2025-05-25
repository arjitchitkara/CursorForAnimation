from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uuid
import os
import logging
from pathlib import Path
import asyncio

from app.api.models import AnimationRequest, SceneResponse
from app.api.llm import get_manim_code_from_llm, fix_manim_code
from app.workers.manim_worker import run_manim_code, VIDEO_DIR

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=SceneResponse)
async def generate_animation(request: AnimationRequest):
    """
    Generate animation from natural language prompt
    """
    scene_id = str(uuid.uuid4())[:8]
    
    try:
        logger.debug(f"Received prompt: {request.prompt}")
        
        # Get Manim code from LLM
        code = await get_manim_code_from_llm(request.prompt)
        logger.debug(f"Generated code from LLM")
        
        # Run the code
        logger.debug(f"Running Manim code")
        result = run_manim_code(code)
        logger.debug(f"Manim result: {result}")
        
        # If failed, try one more time with error feedback
        if not result["success"] and result["error"]:
            logger.debug(f"First attempt failed, trying to fix code with error: {result['error']}")
            fixed_code = await fix_manim_code(code, result["error"])
            result = run_manim_code(fixed_code)
            # Use the fixed code if successful
            if result["success"]:
                code = fixed_code
        
        video_url = None
        if result["success"] and result["video_path"]:
            # Ensure we use a URL path that starts with /static/
            video_path = result["video_path"]
            if not video_path.startswith('/'):
                video_url = f"/{video_path}"
            else:
                video_url = video_path
            
            logger.debug(f"Setting video URL to: {video_url}")
        
        # Return the response
        response = SceneResponse(
            id=scene_id,
            prompt=request.prompt,
            code=code,
            video_url=video_url,
            success=result["success"],
            error=result["error"]
        )
        logger.debug(f"Returning response: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_animation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/videos/{video_id}")
async def get_video(video_id: str):
    """
    Serve a video by its ID from local storage
    """
    video_path = VIDEO_DIR / f"{video_id}.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(str(video_path), media_type="video/mp4") 