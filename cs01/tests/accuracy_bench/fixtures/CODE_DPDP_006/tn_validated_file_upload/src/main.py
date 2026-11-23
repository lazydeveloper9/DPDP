import os
from fastapi import FastAPI, UploadFile, File, HTTPException

app = FastAPI()
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid extension")
    content = await file.read()
    with open(f"uploads/safe_{ext}", "wb") as f:
        f.write(content)
    return {"ok": True}
