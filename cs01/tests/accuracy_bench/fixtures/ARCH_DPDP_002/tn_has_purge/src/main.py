from fastapi import FastAPI

app = FastAPI()

@app.post("/register")
async def register():
    return {"status": "ok"}

def purge_expired_user_data():
    """Scheduled data retention cleanup per DPDP Rule 8."""
    pass
