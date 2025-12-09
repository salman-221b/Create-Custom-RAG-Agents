from datetime import datetime, timezone
import uuid
from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from beanie import PydanticObjectId
from models.botModel import Bot
from models.chatHistoryModel import ChatHistory
from models.tempStorageModel import TempStorage
from utils.crawler import crawl_recursive_batch
from utils import combiningAndChunking
from utils import getGeminiRes
from utils.filesParser import extract_text_from_file
from beanie.operators import Eq
import shutil
from typing import List
import os



async def create_bot(bot: Bot) -> Bot:
    try:
        await bot.insert()
        
        #retrieve chunks from temp storage using session_id
        temp_storage = await TempStorage.find(Eq(TempStorage.session_id, "d224b4bc-d21b-4d73-84c2-cdcc4731b701" )).to_list()
        if not temp_storage:
            return JSONResponse(status_code=404, detail="No temp storage found for this session_id")
        chunks = []
        for storage in temp_storage:
            if storage.dataChunks and isinstance(storage.dataChunks, list):
                chunks.extend(storage.dataChunks)
            else:
                raise ValueError(f"Invalid or missing 'dataChunks' in temp storage document with id: {storage.id}")
        # print("chunks: ", chunks[10])
        
        # Embed and push to Pinecone
        await combiningAndChunking.embed_and_push(
            chunks=chunks,
            botId=str(bot.id)
        )
        return bot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating bot: {str(e)}")

async def get_all_bots_for_user(user_id: str, fetch_links: bool = False):
    try:
        bots = await Bot.find(
            Eq(Bot.user.id, PydanticObjectId(user_id)),
            fetch_links=fetch_links
        ).to_list()
        return bots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bots for user: {str(e)}")


async def get_bot(bot_id: str, fetch_links: bool = True) -> Bot:
    try:
        bot = await Bot.get(PydanticObjectId(bot_id), fetch_links=fetch_links)
        if not bot:
            return JSONResponse(status_code=404, content={"detail": "Bot not found!"})
        return bot
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bot: {str(e)}")
    
    
async def update_bot(bot_id: str, update_data: dict):
    try:
        bot = await Bot.get(PydanticObjectId(bot_id))
        if not bot:
            return JSONResponse(status_code=404, content={"detail": "Bot not found!"})

        update_data = jsonable_encoder(update_data)

        for field, value in update_data.items():
            if hasattr(bot, field):
                setattr(bot, field, value)

        await bot.save()
        return bot

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating bot: {str(e)}")
    
async def delete_bot(bot_id: str):
    try:
        bot = await Bot.get(PydanticObjectId(bot_id))
        if not bot:
            return JSONResponse(status_code=404, content={"detail": "Bot not found!"})
        
        await bot.delete()
        return JSONResponse(status_code=200, content={"detail": "Bot deleted successfully."})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting bot: {str(e)}")
    
async def crawl_website_controller(
    url: str,
    max_depth: int = 3,
    max_concurrent: int = 10,
    page_limit: int = 20
):
    CRAWL_DIR = "crawlOutput"
    try:
        result = await crawl_recursive_batch(
            start_urls=[url],
            max_depth=max_depth,
            max_concurrent=max_concurrent,
            page_limit=page_limit
        )
        print(result)
        
        # Load markdown files from crawlOutput/
        texts = await combiningAndChunking.load_markdown_texts()
        shutil.rmtree(CRAWL_DIR)
        if not texts:
            raise HTTPException(status_code=404, detail="No markdown files found.")

        # Split into chunks
        chunks = await combiningAndChunking.split_into_chunks(texts)

        if not chunks:
            raise HTTPException(status_code=500, detail="Failed to split text into chunks.")
        
        # Store the crawled data in TempStorage
        temp_storage = TempStorage(
            session_id=str(uuid.uuid4()),
            dataChunks=chunks
        )
        await temp_storage.insert()
        return {
            "success": True,
            "message": f"Crawled {result['pages_crawled']} pages.",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawling failed: {str(e)}")

    
    
async def process_uploaded_files(files: List[UploadFile]):
    UPLOAD_DIR = "uploadedFiles"
    try:
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        texts_to_chunk = []
        final_chunks = []

        for file in files:
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            extracted = extract_text_from_file(file_path)
            if extracted:
                if file.filename.endswith(".csv"):
                    final_chunks.extend(extracted if isinstance(extracted, list) else [extracted])
                else:
                    texts_to_chunk.extend(extracted if isinstance(extracted, list) else [extracted])

        shutil.rmtree(UPLOAD_DIR)
        # print("texts to chunks: ", texts_to_chunk)
        # print("\n\n final chunks: ", final_chunks[0])
        if texts_to_chunk:
            non_csv_chunks = await combiningAndChunking.split_into_chunks(texts_to_chunk)
            final_chunks.extend(non_csv_chunks)        
        
        
        if not final_chunks:
            raise HTTPException(status_code=400, detail="No valid text extracted or chunked from files.")

        # Store the processed data in TempStorage
        temp_storage = TempStorage(
            session_id=str(uuid.uuid4()),
            dataChunks=final_chunks
        )
        await temp_storage.insert()
        return {
            "message": f"Successfully processed all files.",
            "chunks": len(final_chunks)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

    
    
    
async def handle_response(query: str, botId: str = None):
    try:
        bot = await Bot.get(PydanticObjectId(botId))
        if not bot:
            return JSONResponse(status_code=404, content={"detail": "Bot not found!"})
        context = await getGeminiRes.retrieve_context(query, botId)
        # print(context)
        geminiResponse = await getGeminiRes.generate_response_with_gemini(query, context, bot.systemPrompt, bot.language)  
        chatMessage = {
            "user_query": query,
            "bot_response": geminiResponse,
            "timestamp": datetime.now(timezone.utc)
        }
        
        # Check if chat history exists for this bot
        chat_history = await ChatHistory.find_one(ChatHistory.bot.id == bot.id)
        # print("chat_history:", chat_history)

        if chat_history:
            chat_history.messages.append(chatMessage)
            await chat_history.save()
        else:
            new_history = ChatHistory(bot=bot.id, messages=[chatMessage])
            await new_history.insert()
        
        return geminiResponse
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
