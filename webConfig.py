from pydantic_settings import BaseSettings
from typing import List

class WebConfig(BaseSettings):
    APP_NAME: str = "Autonomous - MCP"
    ALLOWED_ORIGINS: List[str] = ["*"]
    
config = WebConfig()