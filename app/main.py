from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from dotenv import load_dotenv

from app.api.routes import router as api_router

# Load environment variables
load_dotenv()

app = FastAPI(title="Manim Video Generator")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Create templates directory
templates_dir = Path("app/templates")
templates_dir.mkdir(exist_ok=True)

# Create a templates object
templates = Jinja2Templates(directory=templates_dir)

# Include API routes
app.include_router(api_router, prefix="/api")

# Create a simple HTML form
@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Manim Video Generator</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
                text-align: center;
            }
            textarea {
                width: 100%;
                height: 150px;
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                resize: vertical;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 10px;
            }
            button:hover {
                background-color: #45a049;
            }
            .result {
                margin-top: 20px;
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 4px;
                display: none;
            }
            .error {
                color: red;
                font-weight: bold;
            }
            .video-container {
                margin-top: 20px;
                text-align: center;
            }
            .code-container {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow: auto;
            }
            pre {
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .loading {
                text-align: center;
                margin-top: 20px;
                display: none;
            }
        </style>
    </head>
    <body>
        <h1>Manim Video Generator</h1>
        
        <div>
            <label for="prompt">Enter your scene description:</label>
            <textarea id="prompt" name="prompt" placeholder="Example: A circle that transforms into a square"></textarea>
            <button id="generate">Generate Animation</button>
        </div>
        
        <div class="loading">
            <p>Generating animation... This may take up to 30 seconds.</p>
        </div>
        
        <div class="result" id="result">
            <h2>Result</h2>
            <div id="error" class="error"></div>
            
            <div class="video-container" id="video-container">
                <h3>Generated Animation</h3>
                <video id="video" controls width="640"></video>
            </div>
            
            <div class="code-container">
                <h3>Generated Code</h3>
                <pre id="code"></pre>
            </div>
        </div>
        
        <script>
            document.getElementById('generate').addEventListener('click', async function() {
                const prompt = document.getElementById('prompt').value;
                if (!prompt) {
                    alert('Please enter a scene description');
                    return;
                }
                
                // Show loading
                document.querySelector('.loading').style.display = 'block';
                document.getElementById('result').style.display = 'none';
                
                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            prompt: prompt
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Hide loading
                    document.querySelector('.loading').style.display = 'none';
                    document.getElementById('result').style.display = 'block';
                    
                    if (data.success) {
                        document.getElementById('error').textContent = '';
                        
                        // Display video
                        const videoElement = document.getElementById('video');
                        videoElement.src = data.video_url;
                        document.getElementById('video-container').style.display = 'block';
                        
                        // Display code
                        document.getElementById('code').textContent = data.code;
                    } else {
                        document.getElementById('error').textContent = data.error || 'Failed to generate animation';
                        document.getElementById('video-container').style.display = 'none';
                        document.getElementById('code').textContent = data.code || '';
                    }
                } catch (error) {
                    console.error('Error:', error);
                    document.querySelector('.loading').style.display = 'none';
                    document.getElementById('result').style.display = 'block';
                    document.getElementById('error').textContent = 'An error occurred while generating the animation';
                    document.getElementById('video-container').style.display = 'none';
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_excludes=["app/manim-code/*", "app/static/videos/*"]
    ) 