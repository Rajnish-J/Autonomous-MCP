from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from typing import Literal
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# FastMCP setup
serverName = "runBrowserCheck"
serverSettings = {
    "port": int(os.getenv("PORT", 8005)),
    "sse_path": f"/{serverName}",
}
mcp = FastMCP(serverName, **serverSettings)

@mcp.tool(name=serverName, description="Run a Playwright check on a given URL and summarize it using Gemini.")
async def run_playwright_check(
    url: str,
    check_type: Literal["websearch", "title_only", "summarize"]
) -> dict:
    """
    Run a Playwright check on a URL, with optional Gemini summary.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        if check_type == "websearch":
            await page.fill("input[name='q']", "ai tools")
            await page.keyboard.press("Enter")
            await page.wait_for_selector("h3")
            search_results = await page.locator("h3").all_text_contents()
            await browser.close()

            return {
                "title": await page.title(),
                "top_results": search_results[:5]
            }

        elif check_type == "summarize":
            await page.wait_for_load_state("domcontentloaded")
            body_text = await page.locator("body").inner_text()
            await browser.close()

            # Send to Gemini for summarization
            response = model.generate_content(f"Summarize this page content:\n\n{body_text[:5000]}")
            return {
                "title": await page.title(),
                "summary": response.text
            }

        else:
            title = await page.title()
            await browser.close()
            return {"title": title}
