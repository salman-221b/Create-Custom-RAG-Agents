from beanie import Document, Indexed
from typing_extensions import Annotated
from pydantic import Field
from datetime import datetime, timezone
from pymongo import IndexModel, ASCENDING

class TempStorage(Document):   
    """
    Temporary storage for files and data.
    Automatically expires 30 minutes after creation.
    """
    session_id: str = Field(..., description="Unique session identifier")
    dataChunks: list = Field(..., description="List of data chunks or files")
    
    # TTL index set to expire documents 1800 seconds (30 minutes) after `created_at`
    created_at: datetime = Field(default=datetime.now(timezone.utc), description="Timestamp of when the data was created")

    class Settings:
        name = "temp_storage"  # MongoDB collection name
        indexes = [
            IndexModel(
                [("created_at", ASCENDING)],
                expireAfterSeconds=1800
            )
        ]