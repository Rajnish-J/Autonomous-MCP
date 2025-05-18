from fastapi import APIRouter
from Service.code.aiTestAutomation import AITestAutomation

router = APIRouter()

@router.get("/")
async def run_tests():
    excel_path="user_stories.xlsx"
    automation = AITestAutomation(excel_path)
    await automation.run()

