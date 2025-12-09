import motor.motor_asyncio
from beanie import init_beanie
from dotenv import load_dotenv
import os

from models.userModel import User
from models.botModel import Bot  # include all document models here
from models.chatHistoryModel import ChatHistory
from models.tempStorageModel import TempStorage

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
    print("🔌 Initializing Beanie...")
    await init_beanie(
        database=client[DB_NAME],
        document_models=[User, Bot, ChatHistory, TempStorage]  # Add all models that extend Document
    )
    print("✅ Beanie initialized")
