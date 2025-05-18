from typing import List, Optional
from pydantic import BaseModel


class TestStep(BaseModel):
    step_number: int
    action: str
    element_selector: Optional[str] = None
    input_value: Optional[str] = None
    expected_result: Optional[str] = None
    screenshot_path: Optional[str] = None
    status: str = "Not Run"
    notes: Optional[str] = None


class TestCase(BaseModel):
    id: str
    user_story: str
    steps: List[TestStep] = []
    summary: str = ""
    status: str = "Not Run"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    html_report_path: Optional[str] = None