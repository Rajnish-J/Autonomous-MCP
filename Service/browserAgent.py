import base64
from typing import Any, Dict
from langchain_google_genai import GoogleGenerativeAI
from datetime import datetime
from Models.tests import TestStep
from pathlib import Path
from playwright.async_api import async_playwright
from langchain.schema import HumanMessage

class BrowserAgent:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.llm = GoogleGenerativeAI(model="models/gemini-2.0-flash")
        self.test_results_dir = Path("./utils/test_results")
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