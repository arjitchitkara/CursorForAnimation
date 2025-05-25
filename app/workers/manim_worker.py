import os
import tempfile
import subprocess
import uuid
import shutil
from pathlib import Path

VIDEO_DIR = Path("app/static/videos")

def sanitize_manim_code(code: str) -> str:
    """
    Basic security: ensure only manim imports are allowed
    """
    # Basic regex to check for imports
    lines = code.split("\n")
    sanitized_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        # Allow only imports from manim
        if line_stripped.startswith("import ") and "manim" not in line_stripped:
            continue
        if line_stripped.startswith("from ") and not line_stripped.startswith("from manim"):
            continue
        sanitized_lines.append(line)
    
    return "\n".join(sanitized_lines)

def run_manim_code(code: str) -> dict:
    """
    Runs Manim code in a subprocess and returns the output video path
    """
    # Create unique ID for this render
    render_id = str(uuid.uuid4())[:8]
    
    # Create temp directory and write code to file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Make sure the video output directory exists
        VIDEO_DIR.mkdir(exist_ok=True, parents=True)
        
        # Sanitize the code
        code = sanitize_manim_code(code)
        
        # Write code to a file
        code_file = temp_dir_path / f"scene_{render_id}.py"
        with open(code_file, "w") as f:
            f.write(code)
        
        # Run manim in subprocess
        try:
            cmd = [
                "manim", 
                "-qh",  # High quality
                "--media_dir", temp_dir, 
                str(code_file),
                "Scene0"  # Assuming the scene class is named Scene0
            ]
            
            process = subprocess.Popen(
                cmd, 
                cwd=temp_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(timeout=30)  # 30s timeout
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": stderr,
                    "output": stdout,
                    "video_path": None
                }
            
            # Find the output video
            video_path = list(Path(temp_dir).glob("**/Scene0.mp4"))
            if not video_path:
                return {
                    "success": False,
                    "error": "No video was generated",
                    "output": stdout,
                    "video_path": None
                }
            
            # Copy video to static directory
            output_path = VIDEO_DIR / f"{render_id}.mp4"
            shutil.copy2(video_path[0], output_path)
            
            return {
                "success": True,
                "error": None,
                "output": stdout,
                "video_path": str(output_path.relative_to(Path("app")))
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Rendering timed out (30s)",
                "output": None,
                "video_path": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": None,
                "video_path": None
            } 