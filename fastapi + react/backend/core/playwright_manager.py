import asyncio
import os
import threading
import base64
import logging
from datetime import datetime
from typing import List, Dict, Any
from fastapi import HTTPException
from config.settings import settings
from utils.logging_config import logger

class PlaywrightManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_initialized = False
        self.is_running = False
        self.initialization_lock = threading.Lock()
        self.logs = []
        self.max_logs = 1000  # Keep last 1000 log entries
        
        # Setup custom logger for real-time logs
        self.setup_logger()

    def setup_logger(self):
        """Setup custom logger that captures logs in memory"""
        self.memory_handler = MemoryLogHandler(self)
        self.memory_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.memory_handler.setFormatter(formatter)
        
        # Add to root logger to capture all logs
        logging.getLogger().addHandler(self.memory_handler)

    def add_log(self, level: str, message: str):
        """Add log entry to memory"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        
        # Keep only recent logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Also log to standard logger
        getattr(logger, level.lower(), logger.info)(message)

    async def initialize(self):
        """Initialize Playwright"""
        with self.initialization_lock:
            if self.is_initialized:
                return True
            
            try:
                self.add_log("INFO", "Starting Playwright initialization...")
                
                from playwright.async_api import async_playwright
                
                self.playwright = await async_playwright().start()
                self.add_log("INFO", "Playwright started successfully")
                
                self.browser = await self.playwright.chromium.launch(
                    headless=settings.PLAYWRIGHT_HEADLESS,
                    args=settings.get_browser_args()
                )
                self.add_log("INFO", "Browser launched successfully")
                
                self.context = await self.browser.new_context()
                self.add_log("INFO", "Browser context created")
                
                self.page = await self.context.new_page()
                self.add_log("INFO", "New page created")
                
                self.is_initialized = True
                self.add_log("INFO", "Playwright initialization completed successfully")
                return True
                
            except Exception as e:
                error_msg = f"Failed to initialize Playwright: {str(e)}"
                self.add_log("ERROR", error_msg)
                self.is_initialized = False
                return False

    async def run_user_story(self, user_story: str, steps: List[Dict[str, Any]]):
        """Execute user story with given steps"""
        if not self.is_initialized:
            await self.initialize()
        
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Failed to initialize Playwright")
        
        self.is_running = True
        self.add_log("INFO", f"Starting user story execution: {user_story}")
        
        results = []
        step_number = 1
        
        try:
            for step in steps:
                self.add_log("INFO", f"Executing Step {step_number}: {step.get('description', 'No description')}")
                
                action = step.get('action', '').lower()
                
                if action == 'navigate':
                    url = step.get('url', '')
                    self.add_log("INFO", f"Navigating to: {url}")
                    await self.page.goto(url, wait_until='networkidle')
                    current_url = self.page.url
                    title = await self.page.title()
                    self.add_log("INFO", f"Successfully navigated to: {current_url} - Title: {title}")
                    
                elif action == 'click':
                    selector = step.get('selector', '')
                    self.add_log("INFO", f"Clicking element: {selector}")
                    await self.page.click(selector)
                    self.add_log("INFO", f"Successfully clicked: {selector}")
                    
                elif action == 'type':
                    selector = step.get('selector', '')
                    text = step.get('text', '')
                    self.add_log("INFO", f"Typing '{text}' into: {selector}")
                    await self.page.fill(selector, text)
                    self.add_log("INFO", f"Successfully typed text into: {selector}")
                    
                elif action == 'wait':
                    selector = step.get('selector', '')
                    timeout = step.get('timeout', 30000)
                    self.add_log("INFO", f"Waiting for element: {selector}")
                    await self.page.wait_for_selector(selector, timeout=timeout)
                    self.add_log("INFO", f"Element found: {selector}")
                    
                elif action == 'screenshot':
                    self.add_log("INFO", "Taking screenshot...")
                    screenshot = await self.take_screenshot_internal()
                    self.add_log("INFO", "Screenshot taken successfully")
                    results.append({
                        "step": step_number,
                        "action": "screenshot",
                        "screenshot": screenshot
                    })
                
                # Wait a bit between steps
                await asyncio.sleep(1)
                step_number += 1
                
        except Exception as e:
            error_msg = f"Error in step {step_number}: {str(e)}"
            self.add_log("ERROR", error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        finally:
            self.is_running = False
            self.add_log("INFO", "User story execution completed")
        
        return {
            "user_story": user_story,
            "total_steps": len(steps),
            "results": results,
            "status": "completed"
        }

    async def take_screenshot_internal(self):
        """Internal method to take screenshot"""
        if not self.is_initialized or not self.page:
            raise HTTPException(status_code=503, detail="Playwright not initialized")
        
        screenshot_bytes = await self.page.screenshot(full_page=True)
        return base64.b64encode(screenshot_bytes).decode()

    async def take_screenshot_endpoint(self):
        """Public method for screenshot endpoint"""
        if not self.is_initialized:
            await self.initialize()
        
        if not self.is_initialized:
            raise HTTPException(status_code=503, detail="Failed to initialize Playwright")
        
        self.add_log("INFO", "Taking screenshot via endpoint")
        screenshot = await self.take_screenshot_internal()
        self.add_log("INFO", "Screenshot taken successfully via endpoint")
        
        return {
            "screenshot": screenshot,
            "timestamp": datetime.now().isoformat(),
            "current_url": self.page.url if self.page else None,
            "page_title": await self.page.title() if self.page else None
        }

    def get_logs(self, limit: int = 100):
        """Get recent logs"""
        return {
            "logs": self.logs[-limit:] if limit else self.logs,
            "total_logs": len(self.logs),
            "is_running": self.is_running,
            "is_initialized": self.is_initialized
        }

    async def cleanup(self):
        """Clean up Playwright resources"""
        try:
            self.add_log("INFO", "Starting cleanup...")
            
            if self.page:
                await self.page.close()
                self.add_log("INFO", "Page closed")
            
            if self.context:
                await self.context.close()
                self.add_log("INFO", "Context closed")
            
            if self.browser:
                await self.browser.close()
                self.add_log("INFO", "Browser closed")
            
            if self.playwright:
                await self.playwright.stop()
                self.add_log("INFO", "Playwright stopped")
            
            self.is_initialized = False
            self.add_log("INFO", "Cleanup completed successfully")
            
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            self.add_log("ERROR", error_msg)


class MemoryLogHandler(logging.Handler):
    """Custom log handler that stores logs in memory"""
    
    def __init__(self, playwright_manager):
        super().__init__()
        self.playwright_manager = playwright_manager
    
    def emit(self, record):
        try:
            msg = self.format(record)
            level = record.levelname
            # Only add logs related to our operations
            if any(keyword in msg.lower() for keyword in ['playwright', 'browser', 'page', 'screenshot', 'navigate', 'click', 'type']):
                self.playwright_manager.add_log(level, msg)
        except Exception:
            pass


# Global Playwright manager instance
playwright_manager = PlaywrightManager()