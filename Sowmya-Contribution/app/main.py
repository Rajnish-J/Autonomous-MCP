from fastapi import FastAPI, UploadFile, File
from app.controller import testExecutorController

app = FastAPI()
app.include_router(testExecutorController.router)
