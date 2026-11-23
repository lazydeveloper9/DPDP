from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

app = FastAPI()
app.mount("/public/uploads", StaticFiles(directory="uploads"), name="public_uploads")
