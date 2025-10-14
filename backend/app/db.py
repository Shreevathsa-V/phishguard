import os
import motor.motor_asyncio
from beanie import init_beanie
from app.models import User, Email
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("DATABASE_URL")
DB_NAME = os.getenv("DB_NAME", "phishguard")

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

async def init_db():
    await init_beanie(database=db, document_models=[User, Email])