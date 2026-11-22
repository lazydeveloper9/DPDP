import logging
from fastapi import FastAPI, Request

app = FastAPI()
logger = logging.getLogger(__name__)

# Violation: No consent withdrawal or erasure routes implemented (ARCH-DPDP-001)
@app.post("/register")
async def register(request: Request):
    data = await request.json()
    # Violation: Unguarded PII sent directly to logger (CODE-DPDP-001)
    logger.info(data)
    return {"status": "ok"}
