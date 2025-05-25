from pydantic import BaseModel
from typing import Optional


class AnimationRequest(BaseModel):
    prompt: str
    

class SceneResponse(BaseModel):
    id: str
    prompt: str
    code: str
    video_url: Optional[str] = None
    success: bool
    error: Optional[str] = None 