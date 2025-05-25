from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.playwright_manager import playwright_manager

router = APIRouter()

# Request Models
class UserStoryStep(BaseModel):
    action: str  # navigate, click, type, wait, screenshot
    description: Optional[str] = None
    url: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    timeout: Optional[int] = 30000

class RunPlaywrightRequest(BaseModel):
    user_story: str
    steps: List[UserStoryStep]

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

def get_playwright_manager():
    """Dependency to get the Playwright manager instance"""
    return playwright_manager

@router.post("/run-playwright", response_model=MCPResponse)
async def run_playwright(
    request: RunPlaywrightRequest, 
    pw_manager = Depends(get_playwright_manager)
):
    """
    Execute a user story with Playwright
    
    Example request:
    {
        "user_story": "Login to website and take screenshot",
        "steps": [
            {
                "action": "navigate",
                "description": "Go to login page",
                "url": "https://example.com/login"
            },
            {
                "action": "type",
                "description": "Enter username",
                "selector": "#username",
                "text": "testuser"
            },
            {
                "action": "type",
                "description": "Enter password",
                "selector": "#password",
                "text": "testpass"
            },
            {
                "action": "click",
                "description": "Click login button",
                "selector": "#login-btn"
            },
            {
                "action": "wait",
                "description": "Wait for dashboard",
                "selector": "#dashboard"
            },
            {
                "action": "screenshot",
                "description": "Take final screenshot"
            }
        ]
    }
    """
    try:
        pw_manager.add_log("INFO", f"Received user story: {request.user_story}")
        pw_manager.add_log("INFO", f"Total steps to execute: {len(request.steps)}")
        
        # Convert Pydantic models to dict for processing
        steps_dict = [step.dict() for step in request.steps]
        
        result = await pw_manager.run_user_story(request.user_story, steps_dict)
        
        return MCPResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        error_msg = f"Failed to execute user story: {str(e)}"
        pw_manager.add_log("ERROR", error_msg)
        return MCPResponse(
            success=False,
            error=error_msg
        )

@router.post("/take-screenshot", response_model=MCPResponse)
async def take_screenshot(pw_manager = Depends(get_playwright_manager)):
    """
    Take a screenshot of the current page
    
    Returns base64 encoded screenshot along with page info
    """
    try:
        result = await pw_manager.take_screenshot_endpoint()
        
        return MCPResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        error_msg = f"Failed to take screenshot: {str(e)}"
        pw_manager.add_log("ERROR", error_msg)
        return MCPResponse(
            success=False,
            error=error_msg
        )

@router.get("/logs", response_model=MCPResponse)
async def get_logs(
    limit: Optional[int] = 100,
    pw_manager = Depends(get_playwright_manager)
):
    """
    Get real-time logs from Playwright operations
    
    Parameters:
    - limit: Number of recent logs to return (default: 100, set to 0 for all logs)
    """
    try:
        result = pw_manager.get_logs(limit)
        
        return MCPResponse(
            success=True,
            data=result
        )
        
    except Exception as e:
        return MCPResponse(
            success=False,
            error=f"Failed to get logs: {str(e)}"
        )

@router.get("/status")
async def get_status(pw_manager = Depends(get_playwright_manager)):
    """Get current status of the Playwright service"""
    return {
        "is_initialized": pw_manager.is_initialized,
        "is_running": pw_manager.is_running,
        "total_logs": len(pw_manager.logs),
        "service_status": "ready"
    }