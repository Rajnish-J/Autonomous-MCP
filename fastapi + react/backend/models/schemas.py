from typing import Optional, Any
from pydantic import BaseModel

class NavigateRequest(BaseModel):
    url: str
    wait_for: Optional[str] = "networkidle"
    timeout: Optional[int] = 30000

class ClickRequest(BaseModel):
    selector: str
    timeout: Optional[int] = 30000

class TypeRequest(BaseModel):
    selector: str
    text: str
    delay: Optional[int] = 100

class ScreenshotRequest(BaseModel):
    full_page: Optional[bool] = False
    path: Optional[str] = None

class EvaluateRequest(BaseModel):
    expression: str

class WaitForRequest(BaseModel):
    selector: str
    timeout: Optional[int] = 30000
    state: Optional[str] = "visible"

class MCPResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None