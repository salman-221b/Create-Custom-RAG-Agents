from fastapi import HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from beanie import PydanticObjectId
from models.userModel import User
from pymongo.errors import DuplicateKeyError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from utils import loginHelpers 
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user(user: User) -> User:
    try:
        # Check for existing user with same email (manual check + unique index recommended)
        user.password = pwd_context.hash(user.password)
        await user.insert()
        return user

    except Exception as e:
        if isinstance(e, DuplicateKeyError):
            raise HTTPException(status_code=400, detail="User with this email already exists")
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


async def get_all_users():
    try:
        users = await User.find_all().to_list()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


async def get_user(user_id: str) -> User:
    try:
        print("hello")
        user = await User.get(PydanticObjectId(user_id))
        if user is None:
            return JSONResponse(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


async def update_user(user_id: str, update_data: dict):
    try:
        user = await User.get(PydanticObjectId(user_id))
        if not user:
            return JSONResponse(status_code=404, content={"detail": "User not found!"})

        update_data = jsonable_encoder(update_data)

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        await user.save()
        return user

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user: {str(e)}")


async def delete_user(bot_id: str):
    try:
        bot = await User.get(PydanticObjectId(bot_id))
        if not bot:
            return JSONResponse(status_code=404, content={"detail": "User not found!"})
        
        await bot.delete()
        return JSONResponse(status_code=200, content={"detail": "User deleted successfully."})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")
    
    
    
    
    
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await loginHelpers.authenticate_user(form_data.username, form_data.password)
        if not user:
            return JSONResponse(status_code=401,  content={"detail": "Invalid credentials"})

        access_token = loginHelpers.create_access_token(data={"sub": user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")