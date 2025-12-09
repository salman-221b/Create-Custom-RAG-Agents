from fastapi import APIRouter,Query, UploadFile, File, Form, Body
from models.botModel import Bot
from controllers import botController
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List

router = APIRouter(prefix="/bots", tags=["Bots"])

@router.post("/", response_model=Bot)
async def create_bot(bot: Bot):
    return await botController.create_bot(bot)

@router.get("/{bot_id}", response_model=Bot)
async def get_bot(bot_id: str):
    return await botController.get_bot(bot_id)

@router.get("/user/{user_id}", response_model=list[Bot])
async def list_bots(user_id: str):
    return await botController.get_all_bots_for_user(user_id)


@router.put("/{bot_id}", response_model=Bot)
async def update_bot_endpoint(bot_id: str, update_data: dict = Body(...)):
    return await botController.update_bot(bot_id, update_data)

@router.delete("/{bot_id}")
async def delete_bot(bot_id: str):
    return await botController.delete_bot(bot_id)


class CrawlRequest(BaseModel):
    url: str
    max_depth: Optional[int] = Field(default=3, ge=1, le=10)
    max_concurrent: Optional[int] = Field(default=10, ge=1, le=50)
    page_limit: Optional[int] = Field(default=20, ge=1, le=100)
    
@router.post("/crawl")
async def crawl_endpoint(request: CrawlRequest):
    return await botController.crawl_website_controller(
        url=request.url,
        max_depth=request.max_depth,
        max_concurrent=request.max_concurrent,
        page_limit=request.page_limit
    )



@router.post("/upload-files")
async def upload_files(
    files: List[UploadFile] = File(...)
):
    return await botController.process_uploaded_files(files=files)


class QueryRequest(BaseModel):
    userQuery: str
    
@router.post("/response")
async def generate_response( payload: QueryRequest, 
bot_id: str = Query(..., description="Bot ID for metadata")):
    return await botController.handle_response(query=payload.userQuery, botId=bot_id)