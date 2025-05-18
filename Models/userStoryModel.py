from pydantic import BaseModel

class UserStoryRequest(BaseModel):
    id: int
    user_story: str