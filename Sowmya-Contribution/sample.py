from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.google.com")
        page.locator("[aria-label='Search']").fill("LangChain")
        page.locator("[aria-label='Search']").press("Enter")
        page.locator("a:has-text('LangChain')").first.click()
        page.wait_for_load_state()
        context.close()
        browser.close()

if __name__ == '__main__':
    run()
