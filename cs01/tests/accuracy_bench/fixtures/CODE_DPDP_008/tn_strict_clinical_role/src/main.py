from fastapi import FastAPI, Depends

app = FastAPI()

def require_clinical_user():
    return {"role": "staff_clinical"}

@app.get("/patients/{patient_id}/clinical")
def get_clinical_history(patient_id: str, user = Depends(require_clinical_user)):
    return {"notes": "restricted clinical consultation records"}
