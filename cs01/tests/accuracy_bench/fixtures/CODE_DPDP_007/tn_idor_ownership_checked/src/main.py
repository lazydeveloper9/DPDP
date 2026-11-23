from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()

def get_current_user():
    return {"id": 1, "role": "patient", "patient_id": "1"}

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, current_user = Depends(get_current_user), db = None):
    if current_user.patient_id != patient_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return db.query("Patient").filter(f"patient_id == {patient_id}").first()
