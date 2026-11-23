from fastapi import FastAPI, Depends

app = FastAPI()

def get_current_user():
    return {"id": 1, "role": "patient"}

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, user = Depends(get_current_user), db = None):
    return db.query("Patient").filter(f"patient_id == {patient_id}").first()
