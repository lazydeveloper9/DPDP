from fastapi import FastAPI

app = FastAPI()

@app.post("/register")
async def register_student():
    return {"status": "registered"}
