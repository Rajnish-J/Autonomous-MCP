from langchain_core.output_parsers import StrOutputParser

from MCP import models, prompts

async def storyToPlanAgent(state):
    print("Story to Plan Agent Running...")
    prompt = prompts["story_to_plan"]
    chain = prompt | models.azure_openai | StrOutputParser()
    plan = await chain.ainvoke({"user_story": state["user_story"]})
    return {"plan": plan}

async def planToCodeAgent(state):
    print("Plan to Code Agent Running...")
    prompt = prompts["plan_to_code"]
    chain = prompt | models.azure_openai | StrOutputParser()
    code = await chain.ainvoke({"plan": state["plan"]})
    return {"code": code}