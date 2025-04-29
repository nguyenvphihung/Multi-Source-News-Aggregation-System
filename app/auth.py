from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from functools import wraps
from fastapi.templating import Jinja2Templates
import logging
from app.models import User
from sqlalchemy.orm import Session
from app.database import get_db
import bcrypt  # Import bcrypt để mã hóa mật khẩu
from typing import Optional
import os
import time

router = APIRouter()
templates = Jinja2Templates(directory="templates/")


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    email = request.cookies.get("user_email")
    if email:
        user = db.query(User).filter(User.email == email).first()
        return user
    return None

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("user/FormLogin.html", {"request": request})

# API trang đăng nhập - cập nhật để kiểm tra mật khẩu đã được mã hóa
@router.post("/login")
def login_user(
    Email: str = Form(...),
    Password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == Email).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Email không tồn tại")

    if not bcrypt.checkpw(Password.encode('utf-8'), user.password.encode('utf-8')):
        raise HTTPException(status_code=400, detail="Mật khẩu không chính xác")

    # Xử lý chuyển hướng dựa trên Role
    if user.role.lower() == "admin":
        response = RedirectResponse(url="/admin/1", status_code=302)
    elif user.role.lower() == "user":
        response = RedirectResponse(url="/home", status_code=302)
    elif user.role.lower() == "author":
        response = RedirectResponse(url="/home", status_code=302)
    else:
        raise HTTPException(status_code=403, detail="Bạn không có quyền truy cập")

    # Thiết lập cookie để lưu thông tin user
    response.set_cookie(key="user_email", value=Email, httponly=True, max_age=3600, path="/")
    response.set_cookie(key="user_role", value=user.role, httponly=True, max_age=3600, path="/")

    return response

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("user_email")
    return response

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("user/FormSignUp.html", {"request": request})

# Xử lý đăng ký người dùng - cập nhật để mã hóa password trước khi lưu
@router.post("/register")
def register_user(
    First_name: str = Form(...),
    Last_name: str = Form(...),
    Email: str = Form(...),
    Phone: str = Form(None),
    Password: str = Form(...),
    Newsletter: bool = Form(False),
    Terms: bool = Form(...),
    db: Session = Depends(get_db)
):
    if not Terms:
        raise HTTPException(status_code=400, detail="Bạn phải đồng ý với điều khoản")

    existing_user = db.query(User).filter(User.email == Email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    # Mã hóa mật khẩu sử dụng bcrypt
    hashed_password = bcrypt.hashpw(Password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = User(
        first_name=First_name,
        last_name=Last_name,
        email=Email,
        phone=Phone,
        password=hashed_password,
        newsletter=Newsletter,
        terms_accepted=Terms
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Sau khi đăng ký thành công, chuyển hướng sang trang đăng nhập
    return RedirectResponse(url="/login", status_code=302)

@router.post("/request_author", response_class=JSONResponse)
async def request_author(
    front_card: UploadFile = File(...),
    back_card: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Bạn chưa đăng nhập")
    
    # Tạo thư mục chứa file tạm nếu chưa có
    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    
    current_time = int(time.time())
    front_path = os.path.join(temp_dir, f"{current_user.id}_front_{current_time}.jpg")
    back_path = os.path.join(temp_dir, f"{current_user.id}_back_{current_time}.jpg")
    
    # Lưu file tạm
    with open(front_path, "wb") as f:
        f.write(await front_card.read())
    with open(back_path, "wb") as f:
        f.write(await back_card.read())
    
    logging.info(f"User {current_user.email} đã gửi yêu cầu đăng ký tác giả. File tạm: {front_path}, {back_path}")
    
    # Đánh dấu yêu cầu đăng ký tác giả trong cơ sở dữ liệu
    current_user.author_requested = True
    db.commit()
    
    # Xóa ngay các file tạm sau khi cập nhật
    if os.path.exists(front_path):
        os.remove(front_path)
    if os.path.exists(back_path):
        os.remove(back_path)
    
    return JSONResponse(content={"message": "Yêu cầu đăng ký nhà báo đã được gửi thành công. Vui lòng chờ admin duyệt."})