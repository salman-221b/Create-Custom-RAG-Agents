import os
from pathlib import Path
from typing import List
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import uuid
from dotenv import load_dotenv

load_dotenv()

async def load_markdown_texts(directory: str = "crawlOutput") -> List[str]:
    """
    Loads all markdown files from a directory and returns their content as a list of strings.
    """
    texts = []
    for file in Path(directory).glob("*.md"):
        with open(file, 'r', encoding='utf-8') as f:
            texts.append(f.read())
    return texts

async def split_into_chunks(texts: List[str], chunk_size: int = 1500, overlap: int = 300) -> List[str]:
    """
    Splits each text into chunks with overlap to maintain context.
    """
    chunks = []
    for text in texts:
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
    return chunks



# Load embedding model
async def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")  # Open-source, strong performance

# Initialize Pinecone
async def init_pinecone(api_key: str, index_name: str, dimension: int = 1024, cloud="aws", region="us-east-1"):
    pc = Pinecone(api_key=api_key)

    # Create index if it doesn't exist
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region)
        )

    index = pc.Index(index_name)
    return index

# Embed and upsert chunks
async def embed_and_push(chunks, botId=None, namespace=os.getenv("PINECONE_NAMESPACE")):
    model = await load_embedding_model()
    print("Embedding model loaded.")
    embeddings = model.encode(chunks, batch_size=32, show_progress_bar=True)
    print("Embeddings generated for chunks.")
    pinecone_index = await init_pinecone(
        api_key=os.getenv("PINECONE_API_KEY"),
        index_name=os.getenv("PINECONE_INDEX_NAME"),
        dimension=384,
        cloud="aws",          # or "gcp"
        region="us-east-1"    # or your Pinecone dashboard region
    )
    print("Pinecone initialized.")
    # Prepare records with unique IDs
    to_upsert = [
        (str(uuid.uuid4()), embedding.tolist(), {"text": chunk, "botId": botId})
        for chunk, embedding in zip(chunks, embeddings)
    ]

    # Push to Pinecone
    pinecone_index.upsert(vectors=to_upsert, namespace=namespace)
    print(f"Upserted {len(to_upsert)} chunks to Pinecone.")