# 🎥 VidMind AI — Universal Video Question & Answer Solver

**VidMind AI** is a lightweight, self-hosted multimodal web application that takes any public video URL (YouTube, Instagram Reels, TikTok, X/Twitter, Reddit) and uses **Google Gemini** to watch the video frames, listen to the audio, extract the core question or conversation, and generate clear, accurate answers.

## ✨ Key Features
* **Universal Video Support:** Works with YouTube, Instagram Reels, TikTok, X/Twitter, Reddit, and direct video links via `yt-dlp`.
* **YouTube Fast-Path:** Passes public YouTube URLs directly to Gemini without downloading files locally for near-instant responses.
* **Multimodal Understanding:** Analyzes both spoken dialogue and on-screen text, code, or equations simultaneously.
* **Self-Healing Model Routing:** Automatically discovers active Gemini models on your API key and retries on temporary traffic spikes.
* **Docker Ready:** Fully containerized with `ffmpeg` pre-installed for zero-hassle local or cloud deployment.

## 🛠️ Tech Stack
* **Backend:** Python 3.11, FastAPI, Uvicorn
* **AI Engine:** Google GenAI SDK (`gemini-3.8-flash` / `gemini-3.8-pro`)
* **Media Extraction:** `yt-dlp`, `ffmpeg`
* **Frontend:** Vanilla HTML5, CSS3, JavaScript

## 🚀 Quick Start (Using Docker)

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd vidmind-ai-solver
   ```

2. **Create a `.env` file** in the root folder and add your free Google AI Studio key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Build and run the Docker container:**
   ```bash
   docker build -t vidmind-ai .
   docker run -d -p 7860:7860 --env-file .env --name vidmind-container vidmind-ai
   ```

4. **Open in your browser:**
   Visit **`http://localhost:7860`**, paste any video link, and click **Analyze & Solve Video**.
