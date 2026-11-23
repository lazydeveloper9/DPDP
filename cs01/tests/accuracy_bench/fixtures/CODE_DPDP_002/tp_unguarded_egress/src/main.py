import requests
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/process")
async def process_data(request: Request):
    payload = await request.json()
    response = requests.post("https://api.openai.com/v1/chat", json={"data": payload})
    return {"result": response.status_code}
