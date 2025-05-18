from typing import List, TypedDict

class UserState(TypedDict):
    user_story: str
    plan: str
    code: str
    messages: List[str]
    error: str
    end: bool