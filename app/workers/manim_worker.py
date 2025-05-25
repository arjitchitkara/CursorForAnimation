import os
import tempfile
import subprocess
import uuid
import shutil
import traceback
import logging
import sys
import platform
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Use absolute path to ensure correct location
WORKSPACE_ROOT = Path(__file__).parent.parent.parent.absolute()
VIDEO_DIR = WORKSPACE_ROOT / "app" / "static" / "videos"
CODE_DIR = WORKSPACE_ROOT / "app" / "manim-code"
logger.info(f"Setting VIDEO_DIR to absolute path: {VIDEO_DIR}")
logger.info(f"Setting CODE_DIR to absolute path: {CODE_DIR}")

def check_ffmpeg():
    """Check if FFmpeg is installed and available in the PATH"""
    try:
        # Run a simple ffmpeg command
        if platform.system() == "Windows":
            result = subprocess.run(["where", "ffmpeg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            result = subprocess.run(["which", "ffmpeg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            logger.info(f"FFmpeg found at: {result.stdout.strip()}")
            return True
        else:
            logger.warning("FFmpeg not found in PATH. Videos might not render correctly.")
            return False
    except Exception as e:
        logger.warning(f"Error checking for FFmpeg: {str(e)}")
        return False

# Check FFmpeg on module load
FFMPEG_AVAILABLE = check_ffmpeg()

def sanitize_manim_code(code: str) -> str:
    """
    Basic security: ensure only manim imports are allowed
    and remove Markdown code fences
    """
    # Remove Markdown code fences if they exist
    if code.startswith("```"):
        # Remove first line if it's a code fence
        first_newline = code.find("\n")
        if first_newline > 0:
            code = code[first_newline+1:]
        
        # Remove trailing code fence if it exists
        if "```" in code:
            last_fence = code.rfind("```")
            code = code[:last_fence].rstrip()
    
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
    Runs Manim code and returns the output video path
    """
    # Create unique ID for this render
    render_id = str(uuid.uuid4())[:8]
    
    try:
        # Make sure the directories exist
        VIDEO_DIR.mkdir(exist_ok=True, parents=True)
        CODE_DIR.mkdir(exist_ok=True, parents=True)
        logger.debug(f"Video directory: {VIDEO_DIR}")
        logger.debug(f"Code directory: {CODE_DIR}")
        
        # Sanitize the code
        code = sanitize_manim_code(code)
        
        # Write code to a permanent file
        code_file = CODE_DIR / f"scene_{render_id}.py"
        with open(code_file, "w") as f:
            f.write(code)
        
        logger.debug(f"Saved code to {code_file}")
        logger.debug(f"Code content:\n{code}")
        
        # Create a temp directory for Manim's output (media files)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Run manim in subprocess
            try:
                # Set environment variables to help with FFmpeg issues
                env = os.environ.copy()
                
                # On Windows, sometimes we need to set specific environment variables
                if platform.system() == "Windows":
                    # Try to help Python find FFmpeg if it's in a common location
                    potential_ffmpeg_paths = [
                        "C:\\ffmpeg\\bin",
                        "C:\\Program Files\\ffmpeg\\bin",
                        "C:\\Program Files (x86)\\ffmpeg\\bin"
                    ]
                    
                    # Add potential FFmpeg paths to PATH
                    for ffmpeg_path in potential_ffmpeg_paths:
                        if Path(ffmpeg_path).exists():
                            logger.info(f"Adding potential FFmpeg path to PATH: {ffmpeg_path}")
                            env["PATH"] = f"{ffmpeg_path};{env.get('PATH', '')}"
                
                cmd = [
                    "manim", 
                    "-qh",  # High quality
                    "--media_dir", temp_dir, 
                    str(code_file),
                    "Scene0"  # Assuming the scene class is named Scene0
                ]
                
                logger.debug(f"Running command: {' '.join(cmd)}")
                
                process = subprocess.Popen(
                    cmd, 
                    cwd=str(CODE_DIR),  # Run from code directory
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env  # Use our modified environment
                )
                stdout, stderr = process.communicate(timeout=30)  # 30s timeout
                
                logger.debug(f"Process return code: {process.returncode}")
                logger.debug(f"STDOUT: {stdout}")
                logger.debug(f"STDERR: {stderr}")
                
                if process.returncode != 0:
                    logger.error(f"Manim execution failed with code {process.returncode}")
                    
                    # Try with lower quality if high quality failed
                    if "-qh" in cmd:
                        logger.info("Retrying with lower quality...")
                        cmd[1] = "-ql"  # Low quality
                        
                        process = subprocess.Popen(
                            cmd, 
                            cwd=str(CODE_DIR),
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            text=True,
                            env=env
                        )
                        stdout, stderr = process.communicate(timeout=30)
                        
                        logger.debug(f"Retry process return code: {process.returncode}")
                        logger.debug(f"Retry STDOUT: {stdout}")
                        logger.debug(f"Retry STDERR: {stderr}")
                        
                        if process.returncode != 0:
                            return {
                                "success": False,
                                "error": stderr,
                                "output": stdout,
                                "video_path": None
                            }
                    else:
                        return {
                            "success": False,
                            "error": stderr,
                            "output": stdout,
                            "video_path": None
                        }
                
                # Find the output video - check both Scene0.mp4 and low quality version
                video_paths = list(Path(temp_dir).glob("**/Scene0.mp4"))
                if not video_paths:
                    # Try different quality levels
                    video_paths = list(Path(temp_dir).glob("**/*Scene0*.mp4"))
                
                logger.debug(f"Looking for video in {temp_dir}")
                logger.debug(f"Found videos: {video_paths}")
                
                if not video_paths:
                    logger.error("No video was generated")
                    return {
                        "success": False,
                        "error": "No video was generated",
                        "output": stdout,
                        "video_path": None
                    }
                
                # Copy video to static directory with absolute path
                output_path = VIDEO_DIR / f"{render_id}.mp4"
                logger.debug(f"Copying video from {video_paths[0]} to {output_path}")
                shutil.copy2(video_paths[0], output_path)
                
                # Use a path relative to app for the URL
                relative_path = "static/videos" / Path(f"{render_id}.mp4")
                logger.debug(f"Returning relative path for URL: {relative_path}")
                
                return {
                    "success": True,
                    "error": None,
                    "output": stdout,
                    "video_path": str(relative_path)
                }
                
            except subprocess.TimeoutExpired as e:
                logger.error(f"Rendering timed out: {e}")
                return {
                    "success": False,
                    "error": f"Rendering timed out (30s): {str(e)}",
                    "output": None,
                    "video_path": None
                }
            except Exception as e:
                logger.error(f"Exception in manim subprocess: {str(e)}")
                logger.error(traceback.format_exc())
                return {
                    "success": False,
                    "error": f"Error running Manim: {str(e)}\n{traceback.format_exc()}",
                    "output": None,
                    "video_path": None
                }
    except Exception as e:
        logger.error(f"General exception: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": f"General error: {str(e)}\n{traceback.format_exc()}",
            "output": None,
            "video_path": None
        } 