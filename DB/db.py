from sqlalchemy import JSON, Column, Integer, create_engine, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import sessionmaker
from databases import Database
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://autonomous_mcp_owner:npg_Jd5s4TFvXWCN@ep-sparkling-snowflake-a44wz3au-pooler.us-east-1.aws.neon.tech/autonomous_mcp?sslmode=require")

engine = create_engine(DATABASE_URL, connect_args={})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
database = Database(DATABASE_URL)
Base = declarative_base()

# * Database dependency function
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    check_type = Column(String, nullable=False)
    success = Column(Boolean, default=False)
    data = Column(JSON)
    message = Column(String)
    
class UserStoryRequest(Base):
    __tablename__ = "user_story_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_story = Column(String, nullable=False)
