from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    with open("uploads/file.raw", "wb") as f:
        f.write(content)
    return {"ok": True}
