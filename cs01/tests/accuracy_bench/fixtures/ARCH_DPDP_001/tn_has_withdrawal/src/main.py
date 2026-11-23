import logging
from fastapi import FastAPI, Request

app = FastAPI()
logger = logging.getLogger(__name__)

@app.post("/consent/withdraw")
async def withdraw_consent():
    return {"status": "withdrawn"}

@app.post("/register")
async def register(request: Request):
    return {"status": "ok"}
