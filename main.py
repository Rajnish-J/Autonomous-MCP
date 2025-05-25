"""
AI Automation Testing Application using Playwright and LLMs (Gemini via LangChain)
"""

import os
import pandas as pd
import re
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright, Page, ElementHandle
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import HumanMessage, SystemMessage
import base64
from pathlib import Path
import jinja2
from pydantic import BaseModel

# Set up API key for Google Gemini
# In production, use environment variables or a secure configuration
os.environ["GOOGLE_API_KEY"] = "AIzaSyD53WRAuG3tFtj0FqkHyn-d-7CFLAJXIkk"

# Models for structured data
class TestStep(BaseModel):
    step_number: int
    action: str
    element_selector: Optional[str] = None
    input_value: Optional[str] = None
    expected_result: Optional[str] = None
    screenshot_path: Optional[str] = None
    status: str = "Not Run"
    notes: Optional[str] = None

class TestCase(BaseModel):
    id: str
    user_story: str
    steps: List[TestStep] = []
    summary: str = ""
    status: str = "Not Run"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    html_report_path: Optional[str] = None

class UserStoryExtractor:
    def _init_(self, excel_path: str):
        self.excel_path = excel_path
        
    def extract_user_stories(self) -> List[str]:
        """Extract user stories from the Excel file."""
        try:
            df = pd.read_excel(self.excel_path)
            if 'user_story' not in df.columns:
                raise ValueError("Excel file doesn't contain 'user_story' column")
            
            # Remove NaN values and convert to list
            user_stories = df['user_story'].dropna().tolist()
            return user_stories
        except Exception as e:
            print(f"Error extracting user stories: {e}")
            return []

class PlaywrightCodeGenerator:
    def _init_(self):
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
            json_pattern = r'\[\s*{.}\s\]'
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
                json_match = re.search(r'\[\s*{.}\s\]', direct_result, re.DOTALL)
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

class BrowserAgent:
    def _init_(self):
        self.browser = None
        self.context = None
        self.page = None
        self.llm = GoogleGenerativeAI(model="models/gemini-2.0-flash")
        self.test_results_dir = Path("test_results")
        self.test_results_dir.mkdir(exist_ok=True)
        self.screenshots_dir = self.test_results_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
    async def start(self):
        """Start the Playwright browser."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(self.test_results_dir / "videos")
        )
        self.page = await self.context.new_page()
        
    async def stop(self):
        """Stop the Playwright browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def execute_step(self, step: TestStep) -> TestStep:
        """Execute a single test step in the browser."""
        action = step.action.lower()
        try:
            if action == "navigate":
                await self.page.goto(step.input_value, wait_until="networkidle")
                step.status = "Pass"
                step.notes = f"Navigated to {step.input_value}"
                
            elif action == "click":
                await self.page.wait_for_selector(step.element_selector, state="visible")
                await self.page.click(step.element_selector)
                step.status = "Pass"
                step.notes = f"Clicked on {step.element_selector}"
                
            elif action == "type":
                await self.page.wait_for_selector(step.element_selector, state="visible")
                await self.page.fill(step.element_selector, step.input_value)
                step.status = "Pass"
                step.notes = f"Typed '{step.input_value}' into {step.element_selector}"
                
            elif action == "select":
                await self.page.wait_for_selector(step.element_selector, state="visible")
                await self.page.select_option(step.element_selector, value=step.input_value)
                step.status = "Pass"
                step.notes = f"Selected '{step.input_value}' from {step.element_selector}"
                
            elif action == "assert":
                if "text=" in step.element_selector:
                    text = step.element_selector.replace("text=", "")
                    is_visible = await self.page.is_visible(f"text={text}")
                    if is_visible:
                        step.status = "Pass"
                        step.notes = f"Text '{text}' is visible on the page"
                    else:
                        step.status = "Fail"
                        step.notes = f"Text '{text}' is not visible on the page"
                else:
                    is_visible = await self.page.is_visible(step.element_selector)
                    if is_visible:
                        step.status = "Pass"
                        step.notes = f"Element {step.element_selector} is visible"
                    else:
                        step.status = "Fail"
                        step.notes = f"Element {step.element_selector} is not visible"
                        
            elif action == "wait":
                await self.page.wait_for_timeout(int(step.input_value))
                step.status = "Pass"
                step.notes = f"Waited for {step.input_value}ms"
                
            elif action == "hover":
                await self.page.hover(step.element_selector)
                step.status = "Pass"
                step.notes = f"Hovered over {step.element_selector}"
                
            elif action == "file_upload":
                await self.page.set_input_files(step.element_selector, step.input_value)
                step.status = "Pass"
                step.notes = f"Uploaded file {step.input_value} to {step.element_selector}"
                
            elif action == "screenshot":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"step_{step.step_number}_{timestamp}.png"
                path = self.screenshots_dir / filename
                await self.page.screenshot(path=str(path))
                step.screenshot_path = str(path)
                step.status = "Pass"
                step.notes = f"Screenshot saved to {path}"
                
            else:
                step.status = "Fail"
                step.notes = f"Unknown action: {action}"
                
        except Exception as e:
            step.status = "Fail"
            step.notes = f"Error: {str(e)}"
            # Take a screenshot of the failure
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"error_step_{step.step_number}_{timestamp}.png"
                path = self.screenshots_dir / filename
                await self.page.screenshot(path=str(path))
                step.screenshot_path = str(path)
            except:
                pass
                
        # Always take a screenshot after executing the step (if we don't already have one)
        if not step.screenshot_path:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"step_{step.step_number}_{timestamp}.png"
                path = self.screenshots_dir / filename
                await self.page.screenshot(path=str(path))
                step.screenshot_path = str(path)
            except:
                pass
                
        return step
    
    async def analyze_page_content(self) -> Dict[str, Any]:
        """Use AI to analyze the current page content."""
        # Capture a screenshot
        screenshot_path = self.screenshots_dir / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path))
        
        # Convert screenshot to base64
        with open(screenshot_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        # Get page content
        page_content = await self.page.content()
        
        # Get visible text
        text_content = await self.page.evaluate("""() => {
            return Array.from(document.querySelectorAll('body *'))
                .filter(el => el.offsetParent !== null && !['script', 'style'].includes(el.tagName.toLowerCase()))
                .map(el => el.textContent)
                .join(' ')
                .trim();
        }""")
        
        # Prompt for the LLM
        prompt = f"""
        Analyze this web page and provide a summary of:
        1. The main purpose of the page
        2. Key UI elements visible (forms, buttons, etc.)
        3. Any potential validation or error messages
        4. Current state of the application based on the screenshot
        
        Be concise but thorough.
        """
        
        try:
            # Create message with text and image
            response = await self.llm.ainvoke([
                HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ])
            ])
            
            analysis = response.content
            
            return {
                "summary": analysis,
                "screenshot_path": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "summary": f"Error analyzing page: {str(e)}",
                "screenshot_path": str(screenshot_path),
                "timestamp": datetime.now().isoformat()
            }

class TestReporter:
    def _init_(self):
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath="./"),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Create a simple HTML template if it doesn't exist
        self.template_path = Path("test_report_template.html")
        if not self.template_path.exists():
            self._create_default_template()
            
    def _create_default_template(self):
        """Create a default HTML report template."""
        template_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Automation Test Report</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }
                h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                h2 { color: #2980b9; margin-top: 30px; }
                .summary { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
                .test-info { display: flex; flex-wrap: wrap; }
                .test-info div { margin-right: 30px; margin-bottom: 10px; }
                .steps { width: 100%; border-collapse: collapse; margin: 20px 0; }
                .steps th, .steps td { border: 1px solid #ddd; padding: 10px; text-align: left; }
                .steps th { background-color: #f2f2f2; }
                .step-pass { background-color: #d4edda; }
                .step-fail { background-color: #f8d7da; }
                .screenshot { max-width: 800px; margin: 10px 0; border: 1px solid #ddd; }
                .notes { font-style: italic; color: #666; }
                .status-pass { color: #28a745; font-weight: bold; }
                .status-fail { color: #dc3545; font-weight: bold; }
                .status-not-run { color: #6c757d; font-weight: bold; }
                .page-analysis { background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>AI Automation Test Report</h1>
            
            <div class="summary">
                <h2>Test Summary</h2>
                <div class="test-info">
                    <div><strong>User Story:</strong> {{ test_case.user_story }}</div>
                    <div><strong>Status:</strong> <span class="status-{{ test_case.status|lower }}">{{ test_case.status }}</span></div>
                    <div><strong>Start Time:</strong> {{ test_case.start_time }}</div>
                    <div><strong>End Time:</strong> {{ test_case.end_time }}</div>
                    <div><strong>Duration:</strong> {{ test_case.duration_seconds }} seconds</div>
                </div>
            </div>
            
            {% if test_case.summary %}
            <div class="page-analysis">
                <h2>Test Summary</h2>
                <p>{{ test_case.summary }}</p>
            </div>
            {% endif %}
            
            <h2>Test Steps</h2>
            <table class="steps">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Action</th>
                        <th>Details</th>
                        <th>Expected Result</th>
                        <th>Status</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {% for step in test_case.steps %}
                    <tr class="step-{{ step.status|lower }}">
                        <td>{{ step.step_number }}</td>
                        <td>{{ step.action }}</td>
                        <td>
                            {% if step.element_selector %}Selector: {{ step.element_selector }}{% endif %}
                            {% if step.input_value %}<br>Value: {{ step.input_value }}{% endif %}
                        </td>
                        <td>{{ step.expected_result }}</td>
                        <td class="status-{{ step.status|lower }}">{{ step.status }}</td>
                        <td>{{ step.notes }}</td>
                    </tr>
                    {% if step.screenshot_path %}
                    <tr class="step-{{ step.status|lower }}">
                        <td colspan="6">
                            <img src="{{ step.screenshot_path }}" alt="Step {{ step.step_number }} Screenshot" class="screenshot">
                        </td>
                    </tr>
                    {% endif %}
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """
        with open(self.template_path, "w") as f:
            f.write(template_content)
    
    def generate_report(self, test_case: TestCase) -> str:
        """Generate HTML report for a test case."""
        try:
            template = self.template_env.get_template(self.template_path.name)
            html_content = template.render(test_case=test_case)
            
            # Write to file
            report_dir = Path("test_results/reports")
            report_dir.mkdir(exist_ok=True, parents=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = report_dir / f"report_{test_case.id}_{timestamp}.html"
            
            with open(report_path, "w") as f:
                f.write(html_content)
                
            return str(report_path)
        except Exception as e:
            print(f"Error generating report: {e}")
            return ""

class AITestAutomation:
    def _init_(self, excel_path: str):
        self.excel_path = excel_path
        self.extractor = UserStoryExtractor(excel_path)
        self.code_generator = PlaywrightCodeGenerator()
        self.browser_agent = BrowserAgent()
        self.reporter = TestReporter()
        self.test_cases = []
        
    async def run(self):
        """Run the entire automation process."""
        print("Starting AI Test Automation")
        
        # 1. Extract user stories
        print("Extracting user stories from Excel...")
        user_stories = self.extractor.extract_user_stories()
        print(f"Found {len(user_stories)} user stories")
        
        # Start the browser
        await self.browser_agent.start()
        
        # 2. Process each user story
        for i, story in enumerate(user_stories):
            print(f"\nProcessing user story {i+1}/{len(user_stories)}")
            print(f"User Story: {story}")
            
            # Create a test case
            test_case = TestCase(
                id=f"TC_{i+1}",
                user_story=story,
                start_time=datetime.now().isoformat()
            )
            
            try:
                # Generate test steps
                print("Generating test steps...")
                steps_data = await self.code_generator.generate_test_steps(story)
                
                # Convert to TestStep objects
                test_steps = []
                for step_data in steps_data:
                    test_step = TestStep(
                        step_number=step_data.get("step_number", 0),
                        action=step_data.get("action", ""),
                        element_selector=step_data.get("element_selector"),
                        input_value=step_data.get("input_value"),
                        expected_result=step_data.get("expected_result")
                    )
                    test_steps.append(test_step)
                
                test_case.steps = test_steps
                
                # Execute the steps
                print("Executing test steps...")
                all_passed = True
                for i, step in enumerate(test_case.steps):
                    print(f"Step {i+1}: {step.action}")
                    
                    # Execute the step
                    updated_step = await self.browser_agent.execute_step(step)
                    test_case.steps[i] = updated_step
                    
                    # Update status
                    if updated_step.status != "Pass":
                        all_passed = False
                        print(f"  Status: {updated_step.status} - {updated_step.notes}")
                    else:
                        print(f"  Status: {updated_step.status}")
                    
                    # After each step, analyze the page
                    if updated_step.status == "Pass":
                        analysis = await self.browser_agent.analyze_page_content()
                        print(f"Page Analysis: {analysis['summary'][:100]}...")
                
                # Analyze the final state
                final_analysis = await self.browser_agent.analyze_page_content()
                test_case.summary = final_analysis["summary"]
                
                # Set the test case status
                test_case.status = "Pass" if all_passed else "Fail"
                
            except Exception as e:
                print(f"Error processing user story: {e}")
                test_case.status = "Error"
                test_case.summary = f"An error occurred: {str(e)}"
            
            # Record end time
            test_case.end_time = datetime.now().isoformat()
            test_case.duration_seconds = (
                datetime.fromisoformat(test_case.end_time) - 
                datetime.fromisoformat(test_case.start_time)
            ).total_seconds()
            
            # Generate report
            print("Generating test report...")
            report_path = self.reporter.generate_report(test_case)
            test_case.html_report_path = report_path
            
            # Save the test case
            self.test_cases.append(test_case)
            
            print(f"Test case {test_case.id} completed with status: {test_case.status}")
            print(f"Report generated at: {report_path}")
        
        # Clean up
        await self.browser_agent.stop()
        
        # Print final summary
        print("\n=== Test Automation Summary ===")
        print(f"Total test cases: {len(self.test_cases)}")
        passed = sum(1 for tc in self.test_cases if tc.status == "Pass")
        failed = sum(1 for tc in self.test_cases if tc.status == "Fail")
        errors = sum(1 for tc in self.test_cases if tc.status == "Error")
        print(f"Passed: {passed}, Failed: {failed}, Errors: {errors}")
        
        return self.test_cases
        

# Command-line interface
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Automation Testing with Playwright and LLMs")
    parser.add_argument("--excel", required=True, help="Path to Excel file with user stories")
    args = parser.parse_args()
    
    automation = AITestAutomation(args.excel)
    await automation.run()

if __name__ == "_main_":
    asyncio.run(main())