from fastapi import FastAPI

app = FastAPI()

@app.post("/register")
async def register():
    return {"status": "ok"}
