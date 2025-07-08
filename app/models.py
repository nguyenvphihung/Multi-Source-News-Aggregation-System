from app.database import Base
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean
from datetime import datetime

class Article(Base):
    __tablename__ = "articles"
    
    article_id = Column(String(20), primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    date_posted = Column(DateTime, nullable=True)
    author = Column(String(100), nullable=True)
    source_url = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    type = Column(String(50), nullable=True)
    image_urls = Column(Text, nullable=True)
    video_urls = Column(Text, nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    password = Column(String(255), nullable=False)
    newsletter = Column(Boolean, default=False)
    terms_accepted = Column(Boolean, default=False)
    role = Column(String(50), default="User")  # Mặc định là người dùng
    status = Column(String(50), default="Active")  # Trạng thái kích hoạt tài khoản
    registration_date = Column(DateTime, default=datetime.utcnow)
    avatar_url = Column(String(255), nullable=True)
    author_requested = Column(Boolean, default=False)


class Settings(Base):
    __tablename__ = "settings"
    
    setting_key = Column(String(255), primary_key=True)
    value = Column(String)


# Thêm vào cuối file models.py
class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(String(20), nullable=False)
    user_id = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    parent_id = Column(Integer, nullable=True)  # Cho phép phản hồi lồng nhau
    likes = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, deleted, hidden