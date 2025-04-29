from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Lấy DATABASE_URL từ biến môi trường
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Kiểm tra nếu thiếu DATABASE_URL
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Tạo engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"connect_timeout": 5})

# Tạo session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Khởi tạo base cho ORM
Base = declarative_base()

# Hàm lấy kết nối database
def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối database: {str(e)}")
    finally:
        if db:
            db.close()
