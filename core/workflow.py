from langgraph.graph import StateGraph, END
from .states import UserState
from .agents import storyToPlanAgent, planToCodeAgent

workflow = StateGraph(UserState)

# Add nodes
workflow.add_node("storyToPlanAgent", storyToPlanAgent)
workflow.add_node("planToCodeAgent", planToCodeAgent)

# Set entry point
workflow.set_entry_point("storyToPlanAgent")

# Define flow
workflow.add_edge("storyToPlanAgent", "planToCodeAgent")
workflow.add_edge("planToCodeAgent", END)

# Compile
app = workflow.compile()