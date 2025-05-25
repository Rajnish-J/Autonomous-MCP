from Models.submissionModel import SubmissionRequest, SubmissionResponse
from core import runBrowserCheck;

async def process_submission(request: SubmissionRequest) -> SubmissionResponse:
    """
    
    Process the submission request and return a response.
    
    """
    
    try:
        result = await runBrowserCheck.run_playwright_check(request.url, request.check_type)
        return SubmissionResponse(
            success=True,
            data=result,
            message="Check completed successfully"
        )
    except Exception as e:
        return SubmissionResponse(
            success=False,
            data={},
            message=f"An error occurred: {str(e)}"
        )