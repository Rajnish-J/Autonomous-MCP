import sys
import os

class Settings:
    # Server settings
    HOST = "127.0.0.1"
    PORT = 8000
    RELOAD = True
    LOG_LEVEL = "info"
    
    # Playwright settings
    PLAYWRIGHT_HEADLESS = True
    PLAYWRIGHT_TIMEOUT = 30000
    MAX_INITIALIZATION_RETRIES = 3
    
    # Browser arguments
    BROWSER_ARGS = [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
    ]
    
    # Windows specific browser arguments
    WINDOWS_BROWSER_ARGS = [
        '--single-process',
        '--no-zygote'
    ]
    
    # CORS settings
    CORS_ORIGINS = ["*"]
    CORS_CREDENTIALS = True
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]
    
    @classmethod
    def get_browser_args(cls):
        """Get browser arguments based on platform"""
        args = cls.BROWSER_ARGS.copy()
        if sys.platform == "win32":
            args.extend(cls.WINDOWS_BROWSER_ARGS)
        return args
    
    @classmethod
    def setup_event_loop_policy(cls):
        """Setup event loop policy for Windows compatibility"""
        if sys.platform == "win32":
            import asyncio
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except:
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                except:
                    pass

settings = Settings()