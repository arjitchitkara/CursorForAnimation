from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uuid
import os
from pathlib import Path
import asyncio

from app.api.models import AnimationRequest, SceneResponse
from app.api.llm import get_manim_code_from_llm, fix_manim_code
from app.workers.manim_worker import run_manim_code

router = APIRouter()

@router.post("/generate", response_model=SceneResponse)
async def generate_animation(request: AnimationRequest):
    """
    Generate animation from natural language prompt
    """
    scene_id = str(uuid.uuid4())[:8]
    
    try:
        # Get Manim code from LLM
        code = await get_manim_code_from_llm(request.prompt)
        
        # Run the code
        result = run_manim_code(code)
        
        # If failed, try one more time with error feedback
        if not result["success"] and result["error"]:
            fixed_code = await fix_manim_code(code, result["error"])
            result = run_manim_code(fixed_code)
            # Use the fixed code if successful
            if result["success"]:
                code = fixed_code
        
        # Return the response
        return SceneResponse(
            id=scene_id,
            prompt=request.prompt,
            code=code,
            video_url=f"/static/videos/{os.path.basename(result['video_path'])}" if result["success"] else None,
            success=result["success"],
            error=result["error"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 