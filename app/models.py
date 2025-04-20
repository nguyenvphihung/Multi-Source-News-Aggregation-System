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

    ID = Column(Integer, primary_key=True, index=True)
    FirstName = Column(String(255), nullable=False)
    LastName = Column(String(255), nullable=False)
    Email = Column(String(255), unique=True, nullable=False)
    Phone = Column(String(20), unique=True, nullable=True)
    Password = Column(String(255), nullable=False)
    Newsletter = Column(Boolean, default=False)
    TermsAccepted = Column(Boolean, default=False)
    Role = Column(String(50), default="User")  # Mặc định là người dùng
    Status = Column(String(50), default="Active")  # Trạng thái kích hoạt tài khoản
    RegistrationDate = Column(DateTime, default=datetime.utcnow)
    AvatarUrl = Column(String(255), nullable=True)
    author_requested = Column(Boolean, default=False)


class Settings(Base):
    __tablename__ = "settings"
    
    setting_key = Column(String(255), primary_key=True)
    value = Column(String)