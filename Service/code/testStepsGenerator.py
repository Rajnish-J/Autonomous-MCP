import json
import re
from typing import Dict, List, Any
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


class PlaywrightCodeGenerator:
    def __init__(self):
        # Initialize the LLM
        self.llm = GoogleGenerativeAI(model="models/gemini-2.0-flash")
        
        # System prompt to guide the LLM
        self.system_prompt = """
        You are an expert test automation engineer. Your task is to convert user stories into precise Playwright test steps.
        
        For each user story, generate a JSON array of test steps. Each step should include:
        - step_number: The sequence number of the step
        - action: One of "navigate", "click", "type", "select", "assert", "wait", "hover", "file_upload", "screenshot"
        - element_selector: CSS or XPath selector for the element (when applicable)
        - input_value: Value to input (for type actions)
        - expected_result: Expected outcome of the step (for assertions)
        
        DO NOT include actual Python code, just the JSON array of steps.
        Example format:
        [
            {
                "step_number": 1,
                "action": "navigate",
                "element_selector": null,
                "input_value": "https://example.com",
                "expected_result": "Page loads successfully"
            },
            {
                "step_number": 2,
                "action": "type",
                "element_selector": "#username",
                "input_value": "testuser",
                "expected_result": "Username is entered"
            }
        ]
        """
        
        # Set up the prompt template
        self.template = """
        User Story: {user_story}
        
        Generate a detailed sequence of test steps that can be automated with Playwright to verify this user story.
        Focus on concrete actions like navigation, clicks, typing, and assertions.
        """
        self.prompt = PromptTemplate(
            input_variables=["user_story"],
            template=self.template
        )
        
        # Create the chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        
    async def generate_test_steps(self, user_story: str) -> List[Dict[str, Any]]:
        """Generate test steps based on the user story."""
        try:
            # First, get the AI to generate the steps description
            result = await self.chain.arun(user_story=user_story)
            
            # Parse the result to extract the JSON part
            # This is a bit tricky as the model might return additional text
            json_pattern = r'\[\s*{.*}\s*\]'
            json_match = re.search(json_pattern, result, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                steps = json.loads(json_str)
                return steps
            else:
                # If no JSON is found, try to generate it more directly
                direct_prompt = f"""
                Convert this user story into a JSON array of test steps:
                {user_story}
                
                Return ONLY the JSON array with this format:
                [
                    {{"step_number": 1, "action": "navigate", "element_selector": null, "input_value": "URL", "expected_result": "outcome"}},
                    ...
                ]
                """
                direct_result = await self.llm.ainvoke(direct_prompt)
                # Extract JSON from the result
                json_match = re.search(r'\[\s*{.*}\s*\]', direct_result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                else:
                    raise ValueError("Failed to generate JSON test steps")
        except Exception as e:
            print(f"Error generating test steps: {e}")
            # Return a basic step as fallback
            return [
                {
                    "step_number": 1,
                    "action": "navigate",
                    "element_selector": None,
                    "input_value": "https://example.com",
                    "expected_result": "Error in test step generation"
                }
            ]
