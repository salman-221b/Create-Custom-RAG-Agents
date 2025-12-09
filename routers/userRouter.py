from fastapi import APIRouter, Body
from fastapi.security import OAuth2PasswordRequestForm
from models.userModel import User
from controllers import userController
from pydantic import BaseModel, EmailStr
from fastapi import Depends
from middleware.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])



@router.post("/", response_model=User)
async def create_user(user: User):
    return await userController.create_user(user)



@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    return await userController.get_user(user_id)



@router.get("/", response_model=list[User])
async def list_users(current_user: User = Depends(get_current_user)):
    return await userController.get_all_users()


@router.put("/{user_id}", response_model=User)
async def update_user_endpoint(user_id: str, update_data: dict = Body(...)):
    return await userController.update_user(user_id, update_data)


@router.delete("/{user_id}")
async def delete_user(user_id: str):
    return await userController.delete_user(user_id)



class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await userController.login(form_data)