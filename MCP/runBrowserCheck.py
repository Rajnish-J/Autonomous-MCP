from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from typing import Literal
import os

serverName = "runBrowserCheck"
serverSettings = {
    "port" : os.getenv("PORT", 8005),
    "sse_path" : f"/{serverName}",
}

mcp = FastMCP(serverName, **serverSettings)

@mcp.tool(name=serverName, description="Run a Playwright check on a given URL.")
async def run_playwright_check(
    url: str,
    check_type: Literal["websearch", "title_only"]
) -> dict:
    
    """
    Runs a Playwright check on a given URL.

    Args:
        url: The webpage URL to open.
        check_type: The type of check to perform. Use 'websearch' to search "ai tools" on Google, or 'title_only' to just return the page title.

    Returns:
        A dictionary with the page title and optionally the top search result titles.
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

        title = await page.title()
        await browser.close()
        return {"title": title}
