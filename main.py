from fastapi import FastAPI, UploadFile, Form, File
from typing import List
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from workflows.video_graph import generate_video
import uuid
import os

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/generate-video/")
async def create_video_endpoint(
    text: str = Form(...),
    images: List[UploadFile] = File(...)
):
    # ✅ Ensure output directory exists
    output_dir = "static/output"
    os.makedirs(output_dir, exist_ok=True)

    # ✅ Unique output file name
    output_filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(output_dir, output_filename)

    # ✅ Save uploaded images locally

    image_dir = "static/images"
    os.makedirs(image_dir, exist_ok=True)

    image_paths = []
    for img in images:
        img_filename = f"temp_{uuid.uuid4()}_{img.filename}"
        img_path = os.path.join(image_dir, img_filename)
        with open(img_path, "wb") as f:
            f.write(await img.read())
        image_paths.append(img_path)

    # ✅ Call your video generation logic
    await generate_video(text, image_paths, output_path)

    # ✅ Cleanup temporary images
    for path in image_paths:
        if os.path.exists(path):
            os.remove(path)

    # ✅ Return public URL or file path
    return {
        "message": "Video created successfully",
        "output": f"/{output_path}"  # Serve via StaticFiles
    }