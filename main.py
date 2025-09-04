from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from extractor import extract_text_from_file, extract_candidate_info

app = FastAPI()

# Allow Angular frontend (adjust origin as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your AngularJS app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # Save file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text & info
        text = extract_text_from_file(file_path)
        extracted_info = extract_candidate_info(text)

        return {"status": "success", "data": extracted_info}

    except Exception as e:
        return {"status": "error", "message": str(e)}
