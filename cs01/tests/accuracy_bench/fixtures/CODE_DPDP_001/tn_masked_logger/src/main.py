import logging
from fastapi import FastAPI, Request

app = FastAPI()
logger = logging.getLogger(__name__)

def mask_pii(val):
    return "[REDACTED]"

@app.post("/register")
async def register(request: Request):
    data = await request.json()
    logger.info(mask_pii(data))
    return {"status": "ok"}
