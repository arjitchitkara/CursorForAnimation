import os
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek-r1:free")

SYSTEM_PROMPT = """You are an expert Manim script writer.
Return valid Python 3.11 code that imports from manim, defines
class Scene0(Scene) with construct().
The scene must run in ≤ 15 seconds, 1920×1080, and use only core Manim primitives.
Respond with code only."""

async def get_manim_code_from_llm(prompt: str) -> str:
    """
    Sends a prompt to the LLM via OpenRouter API and gets Manim code in return
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not found in environment variables")
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://manim-video-generator.com"  # Update with your domain
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=data,
            timeout=60.0
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"]
        
async def fix_manim_code(code: str, error: str) -> str:
    """
    Sends the error to the LLM to get fixed Manim code
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key not found in environment variables")
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://manim-video-generator.com"  # Update with your domain
    }
    
    data = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Generate Manim code for me."},
            {"role": "assistant", "content": code},
            {"role": "user", "content": f"Here is the traceback. Fix all errors and resend only the corrected code.\n\n{error}"}
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=data,
            timeout=60.0
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")
            
        result = response.json()
        return result["choices"][0]["message"]["content"] 