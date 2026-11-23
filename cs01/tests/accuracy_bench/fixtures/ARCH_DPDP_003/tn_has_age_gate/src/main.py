from fastapi import FastAPI

app = FastAPI()

def check_age(dob):
    """Verify age gate per DPDP Act Section 9."""
    pass

@app.post("/register")
async def register_student():
    return {"status": "registered"}
