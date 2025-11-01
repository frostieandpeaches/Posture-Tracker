import os
import uuid
import json
import time
import logging
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from redis import Redis
from rq import Queue
from processing.posture_analysis import analyze_posture

app = FastAPI()

# === Configuration ===
HOST = os.getenv("HOST", "localhost")
PORT = os.getenv("PORT", "8000")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
RESULT_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

# Serve processed video files
app.mount("/results", StaticFiles(directory=RESULT_DIR), name="results")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Redis Queue ===
redis_conn = Redis(host="redis", port=6379)
q = Queue(connection=redis_conn)

logging.basicConfig(level=logging.INFO)
logging.info(f"UPLOAD_DIR={UPLOAD_DIR}")
logging.info(f"RESULT_DIR={RESULT_DIR}")

# === Upload Endpoint ===
@app.post("/upload")
async def upload_file(file: UploadFile):
    file_id = str(uuid.uuid4())
    upload_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp4")

    try:
        with open(upload_path, "wb") as f:
            f.write(await file.read())
        logging.info(f"✅ File saved to: {upload_path}")
    except Exception as e:
        logging.error(f"❌ Failed to save file: {e}")
        return {"error": f"Failed to save file: {str(e)}"}

    try:
        job = q.enqueue(analyze_posture, upload_path, file_id)
        logging.info(f"🧠 Job enqueued: {job.id}")
        return {"job_id": job.id, "file_id": file_id}
    except Exception as e:
        logging.error(f"❌ Failed to enqueue job: {e}")
        return {"error": f"Failed to enqueue job: {str(e)}"}


# === Check job status ===
@app.get("/status/{job_id}")
def get_status(job_id: str):
    from rq.job import Job
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        logging.info(f"ℹ Job {job_id} status: {job.get_status()}")
        return {"job_id": job_id, "status": job.get_status()}
    except Exception as e:
        logging.error(f"❌ Failed to fetch status: {e}")
        return {"error": str(e)}


# === Get processing result ===
@app.get("/api/results/{file_id}")
async def get_result(file_id: str, request: Request):
    result_path = os.path.join(RESULT_DIR, f"{file_id}.json")
    video_filename = f"{file_id}_overlay_fixed.mp4"
    video_path = os.path.join(RESULT_DIR, video_filename)

    # Wait for processing completion
    timeout = 30
    waited = 0
    while not os.path.exists(result_path) and waited < timeout:
        time.sleep(2)
        waited += 2

    if not os.path.exists(result_path):
        return {"status": "processing"}

    with open(result_path, "r") as f:
        data = json.load(f)

    # Return accessible URL (mounted via /results)
    base_url = str(request.base_url).rstrip("/")
    video_url = f"{base_url}/results/{video_filename}"

    logging.info(f"✅ Returning result for {video_url}")
    return {"status": "complete", "result": data, "video_url": video_url}
