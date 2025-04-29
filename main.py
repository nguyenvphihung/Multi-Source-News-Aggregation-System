from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.admin import router as admin_router  # Import module admin
from app.user import router as user_router  # Import module user
from app.auth import router as auth_router  # Import module auth
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Đăng ký các route cho Admin, User & Auth
app.include_router(admin_router)
app.include_router(user_router)
app.include_router(auth_router)
