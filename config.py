import os
from dotenv import load_dotenv

load_dotenv()

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/taskr")

    DB_BACKEND = os.getenv("DB_BACKEND", "mongo").lower()

    SQLITE_PATH = os.getenv("SQLITE_PATH", "taskr.sqlite3")