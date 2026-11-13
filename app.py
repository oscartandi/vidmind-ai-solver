import os
import time
import uuid
import yt_dlp
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, Form
from fastapi.responses import FileResponse, HTMLResponse


load_dotenv()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

app = FastAPI(title="VidMind AI — Fast Video Q&A Solver")


class VideoRequest(BaseModel):
    url: str
    question: str = ""


def is_youtube_url(url: str) -> bool:
    lower_url = url.lower()
    return "://youtube.com" in lower_url or "youtu.be/" in lower_url


def download_video(url: str, output_path: str):
    """Downloads a lightweight 480p mp4 with a 15-second timeout so it never hangs."""
    ydl_opts = {
        "outtmpl": output_path,
        "format": "best[height<=480][ext=mp4]/worst[ext=mp4]/best",
        "noplaylist": True,
        "socket_timeout": 15,
        "quiet": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def get_available_gemini_models():
    preferred = [
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-3.8-pro",
    ]
    available = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if (
                "gemini" in name
                and "embedding" not in name
                and "imagen" not in name
                and "veo" not in name
                and "tts" not in name
            ):
                available.append(name)
    except Exception:
        return preferred

    ordered = [m for m in preferred if m in available]
    for m in available:
        if m not in ordered:
            ordered.append(m)
    return ordered or preferred


def generate_with_retry(content_input, prompt: str):
    models_to_try = get_available_gemini_models()
    last_error = None

    for model_name in models_to_try:
        print(f"👉 Trying Gemini model: {model_name}")
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[content_input, prompt],
                    config=types.GenerateContentConfig(temperature=0.2),
                )
                return response.text
            except Exception as e:
                last_error = e
                error_str = str(e)
                print(f"⚠️ Model {model_name} error: {error_str}")
                if "503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str:
                    time.sleep(1.5)
                    continue
                elif "404" in error_str or "NOT_FOUND" in error_str or "400" in error_str:
                    break
                else:
                    raise e

    if last_error:
        raise last_error
    raise RuntimeError("No available Gemini models responded.")


@app.get("/")
def home():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(base_dir, "index.html"))

@app.post("/analyze-form", response_class=HTMLResponse)
def analyze_video_form(url: str = Form(...), question: str = Form("")):
    result = analyze_video(VideoRequest(url=url, question=question))
    answer_html = result["answer"].replace("\n", "<br>")
    return f"""
    <html>
    <body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 40px; max-width: 760px; margin: auto; line-height: 1.6;">
        <a href="/" style="color: #38bdf8; text-decoration: none; font-weight: bold;">← Back to VidMind AI</a>
        <div style="margin-top: 20px; background: #1e293b; padding: 24px; border-radius: 14px; border: 1px solid #334155;">
            <h2 style="color: #38bdf8; margin-top: 0;">💡 AI Extraction & Solution</h2>
            <div>{answer_html}</div>
        </div>
    </body>
    </html>
    """


@app.post("/analyze")
def analyze_video(payload: VideoRequest):
    print(f"\n📩 Received request for URL: {payload.url}")
    temp_file = f"temp_{uuid.uuid4().hex}.mp4"
    uploaded_file = None

    prompt = payload.question.strip() or (
        "Watch and listen carefully to this video. "
        "### 1. Extracted Question or Topic\n"
        "State the exact question asked, riddle presented, or main topic of conversation.\n\n"
        "### 2. Context Summary\n"
        "Briefly summarize what happens or is discussed in the video.\n\n"
        "### 3. Best Solution & Answer\n"
        "Provide the clearest, most accurate answer or step-by-step solution."
    )

    try:
        if is_youtube_url(payload.url):
            print("⚡ Using YouTube direct fast-path...")
            yt_part = types.Part.from_uri(file_uri=payload.url.strip(), mime_type="video/mp4")
            answer_text = generate_with_retry(yt_part, prompt)
            print("✅ Done!")
            return {"answer": answer_text}

        print("⬇️ Downloading video...")
        download_video(payload.url, temp_file)
        if not os.path.exists(temp_file):
            return {"answer": "❌ **Download Failed:** Could not retrieve the video. Make sure the link is public."}

        print("☁️ Uploading video to Gemini...")
        uploaded_file = client.files.upload(file=temp_file)

        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = client.files.get(name=uploaded_file.name)

        if uploaded_file.state.name != "ACTIVE":
            return {"answer": "❌ **Processing Failed:** Gemini could not process this video format."}

        answer_text = generate_with_retry(uploaded_file, prompt)
        print("✅ Done!")
        return {"answer": answer_text}

    except Exception as e:
        print(f"❌ Exception: {e}")
        return {"answer": f"❌ **Error:** {str(e)}"}

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception:
                pass

"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
"""
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

