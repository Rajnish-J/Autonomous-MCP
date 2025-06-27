from fastapi import FastAPI, UploadFile, File
from app.controller import test_executor

app = FastAPI()
app.include_router(test_executor.router)


