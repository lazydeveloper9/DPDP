from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

app = FastAPI()
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
