from langchain_mcp_adapters.client import MultiServerMCPClient
from .models import azure_openai
from langgraph.prebuilt import create_react_agent
from .utils import mcpResponseFormatter
import os
import json

async def playwrightToolClient(prompt):
    config_path = os.path.join(os.path.dirname(__file__), 'servers/playwright/config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    async with MultiServerMCPClient(config) as client:
        agent = create_react_agent(azure_openai, prompt, client.get_tools())
        response = await agent.ainvoke({})
        formatted = mcpResponseFormatter(response['messages'])
        return formatted.get('aiResponse', '')