import re
from fastapi import HTTPException
from core.mcpServers.PlayWright.server import generate_playwright_code

def validate_user_story(user_story: str):
    if not user_story or len(user_story.strip()) < 10:
        raise HTTPException(status_code=400, detail="User story must be at least 10 characters long.")
    if not re.search(r"(login|navigate|click|fill)", user_story.lower()):
        raise HTTPException(status_code=400, detail="User story must include actionable verbs like 'login', 'navigate', etc.")

def run_playwright_generation(user_story: str):
    validate_user_story(user_story)
    return generate_playwright_code(user_story)