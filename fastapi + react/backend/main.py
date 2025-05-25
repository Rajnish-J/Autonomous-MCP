import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import configuration and setup
from config.settings import settings
from utils.logging_config import logger
from core.playwright_manager import playwright_manager
from api.endpoints import router

# CRITICAL: Set event loop policy BEFORE any other imports that might use asyncio
settings.setup_event_loop_policy()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting application...")
    
    # Startup
    try:
        await playwright_manager.initialize()
        if playwright_manager.is_initialized:
            logger.info("Application started with Playwright support")
        else:
            logger.warning("Application started without Playwright support")
    except Exception as e:
        logger.warning(f"Playwright initialization failed: {str(e)}")
        logger.info("Application will continue in limited mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await playwright_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Playwright MCP Server",
    description="Model Context Protocol server with Playwright browser automation",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    # Ensure event loop policy is set before running
    settings.setup_event_loop_policy()
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL
    )