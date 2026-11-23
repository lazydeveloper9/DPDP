import logging
from fastapi import FastAPI, Request

app = FastAPI()
logger = logging.getLogger(__name__)

def mask_pii(val):
    return "[REDACTED]"

@app.post("/process")
async def process_data(request: Request):
    payload = await request.json()
    safe_payload = mask_pii(payload)
    logger.info(safe_payload)
    return {"status": "ok"}
