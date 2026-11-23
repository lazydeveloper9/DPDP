import logging
from fastapi import FastAPI, Request

app = FastAPI()
logger = logging.getLogger(__name__)

@app.post("/register")
async def register(request: Request):
    return {"status": "ok"}
