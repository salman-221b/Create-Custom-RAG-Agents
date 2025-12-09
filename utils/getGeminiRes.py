import os
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

async def load_query_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


async def retrieve_context(query, botId=None, namespace=os.getenv("PINECONE_NAMESPACE")):
    model = await load_query_embedding_model()

    query_embedding = model.encode([query])[0].tolist()
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    pinecone_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))
    results = pinecone_index.query(
        vector=query_embedding,
        top_k=5,
        namespace=namespace,
        include_metadata=True,
        filter={"botId": {"$eq": botId}}
        
    )
    context_chunks = [match['metadata']['text'] for match in results['matches']]
    print(f"Retrieved {len(context_chunks)} context chunks for query: {query}")
    return context_chunks

async def generate_response_with_gemini(user_query, context_chunks, systemPrompt, language):
    client = genai.Client()
    context_str = "\n\n---\n\n".join(context_chunks)
    prompt = f"""
            {systemPrompt}
            
            Use the context below to answer the user's question.
            if the context does not contain the answer, say "The data that you have provided does not contain any information regarding your query. Please try again!!".

            Respond in {language} only.
            
            Context:
            {context_str}
            """

    response = client.models.generate_content(model="gemini-2.0-flash", 
                                        config=types.GenerateContentConfig(
                                        system_instruction=prompt),
                                        contents=user_query)
    return response.text.strip()