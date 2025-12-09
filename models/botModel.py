from beanie import Document, Link
from pydantic import Field
from typing import Optional
from models.userModel import User

class Bot(Document):
    """
    Bot document linked to a User.
    """
    name: str = Field(..., description="Bot name")
    language: Optional[str] = Field("English", description="Description of the bot")
    systemPrompt: str = Field(..., description="System Prompt for the chatbot")
    user: Link[User] = Field(..., description="Reference to the owner user")

    class Settings:
        name = "bots"  # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "name": "SupportBot",
                "language": "Engilsh",
                "systemPrompt": "You are a helpful assistant.",
                "user": "64f9a2b6e1f84a9c4c36c998"
            }
        }
