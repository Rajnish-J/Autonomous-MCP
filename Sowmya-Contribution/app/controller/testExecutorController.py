from fastapi import APIRouter, UploadFile, File
from app.service.testService import process_excel_file

router = APIRouter()

@router.post("/execute-tests/")
async def execute_tests(file: UploadFile = File(...)):
    result = await process_excel_file(file)
    return result
