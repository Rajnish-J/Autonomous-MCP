from fastapi import APIRouter, HTTPException
from core.mcpServers.PlayWright.server import generate_playwright_code
from 
from Models.userStoryModel import UserStoryRequest

router = APIRouter()

@router.post("/generate-code")
async def generate_code(request: UserStoryRequest):
    try:
        result = generate_playwright_code(request.user_story)
        return {
            "status": "success",
            "data": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")