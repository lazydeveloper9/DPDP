from fastapi import FastAPI

app = FastAPI()

def log_audit(action, target_resource_id="1"):
    pass

@app.get("/records/{record_id}")
def get_record(record_id: str):
    log_audit(action="RECORD_READ", target_resource_id=record_id)
    return {}
