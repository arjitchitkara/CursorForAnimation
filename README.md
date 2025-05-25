# Manim Video Generator

A simple web application that generates Manim animations from natural language descriptions.

## Features

- Generate animations from text descriptions
- View animations in-browser
- See generated Manim code
- Error recovery with automatic code fixing

## Setup

1. Clone the repository

```bash
git clone https://github.com/yourusername/manim-video-generator.git
cd manim-video-generator
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Install Manim and its dependencies

Follow the [official Manim installation guide](https://docs.manim.community/en/stable/installation.html) for your OS.

For Windows, this generally means:
- Install Cairo, FFmpeg, and LaTeX
- Install MinGW or Visual C++ Build Tools

4. Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` with your OpenRouter API key. You can get a free API key from [OpenRouter](https://openrouter.ai).

## Usage

1. Start the server

```bash
python -m app.main
```

2. Open your browser and navigate to http://localhost:8000

3. Enter a scene description and click "Generate Animation"

## Example Prompts

- "A circle that transforms into a square"
- "The Pythagoras theorem visualized geometrically"
- "A 3D cube rotating in space"

## Project Structure

```
app/
├── api/             # API endpoints
├── workers/         # Manim worker code
├── static/          # Static assets
│   └── videos/      # Generated videos
├── templates/       # HTML templates
└── main.py          # Main application entry point
```

## License

MIT

