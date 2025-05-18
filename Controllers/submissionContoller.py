from fastapi import APIRouter
from Models.submissionModel import SubmissionResponse, SubmissionRequest
from Service.code.submissionService import process_submission

router = APIRouter()

@router.post("/run", response_model=SubmissionResponse)
async def run_submission(request: SubmissionRequest):
    """
    
    Endpoint to run a submission check
    
    """
    return await process_submission(request)