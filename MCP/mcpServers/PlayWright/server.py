from langgraph.graph import StateGraph, END
from MCP.states import UserState
from MCP.agents import storyToPlanAgent, planToCodeAgent

# Define simple graph
workflow = StateGraph(UserState)
workflow.add_node("storyToPlanAgent", storyToPlanAgent)
workflow.add_node("planToCodeAgent", planToCodeAgent)

workflow.set_entry_point("storyToPlanAgent")
workflow.add_edge("storyToPlanAgent", "planToCodeAgent")
workflow.add_edge("planToCodeAgent", END)

app = workflow.compile()

def generate_playwright_code(user_story: str):
    """
    Server-side function to generate Playwright code from a user story.
    """
    initial_state = {
        "user_story": user_story,
        "plan": "",
        "code": "",
        "messages": [],
        "end": False
    }

    result = app.invoke(initial_state)
    return {
        "user_story": user_story,
        "plan": result.get("plan"),
        "code": result.get("code")
    }