from beanie import Document
from pydantic import EmailStr, Field
from beanie.odm.fields import Indexed
from typing_extensions import Annotated


class User(Document):
    """
    User document stored in MongoDB, using Beanie.
    """
    name: str = Field(..., description="Full name of the user")
    email: Annotated[EmailStr, Indexed(unique=True)]
    password: str = Field(..., description="password of the user")

    class Settings:
        name = "users"  # MongoDB collection name

    class Config:
        json_schema_extra = {
            "example": {
                "name": "john doe",
                "email": "john.doe@example.com",
                "password": "12345"
            }
        }
        