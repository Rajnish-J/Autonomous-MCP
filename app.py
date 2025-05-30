from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from webConfig import config
from DB.db import engine, Base

import Controllers.submissionContoller as submission
import Controllers.testController as tests
import Controllers.playwright_controller as playwright

app = FastAPI(title=config.APP_NAME)
Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins = config.ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

def create_db():
    Base.metadata.create_all(bind=engine)
    print("Database and tables created successfully!")
    
app.include_router(submission.router, prefix="/submission", tags=["submission"])
app.include_router(tests.router, prefix="/tests", tags=["tests"])
app.include_router(playwright.router, prefix="/playwright", tags=["playwright"])