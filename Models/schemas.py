from pydantic import BaseModel

class SubmissionRequest(BaseModel):
    url: str
    check_type: str

class SubmissionResponse(BaseModel):
    success: bool
    data: dict
    message: str
