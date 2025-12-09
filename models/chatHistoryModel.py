from beanie import Document, Link
from pydantic import Field
from typing import Optional
from models.botModel import Bot

class ChatHistory(Document):
    """
    Chat history document linked to a Bot.
    """
    bot: Link[Bot] = Field(..., description="Reference to the bot associated with this chat history")
    messages: list[dict] = Field(..., description="List of messages in the chat history")

    class Settings:
        name = "chat_history"  # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "bot": "64f9a2b6e1f84a9c4c36c998",
                "messages":[
                    {
                        "user_query": "What is the weather today?",
                        "bot_response": "The weather today is sunny with a high of 75°F.",
                        "timestamp": "2023-10-01T12:00:00Z"
                    }
                ]
            }
        }
