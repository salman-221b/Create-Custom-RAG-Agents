from fastapi import FastAPI
from routers import userRouter, botRouter
from utils.db import init_db

    
app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await init_db()



# Register routers
app.include_router(userRouter.router)
app.include_router(botRouter.router)

# Optional root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI MongoDB User API"}