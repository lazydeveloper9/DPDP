from fastapi import FastAPI

app = FastAPI()

def log_audit(action, target_resource_id=None):
    pass

@app.get("/records")
def list_records():
    log_audit(action="BULK_RECORD_QUERY", target_resource_id=None)
    return []
