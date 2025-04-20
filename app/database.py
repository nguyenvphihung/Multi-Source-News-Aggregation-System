from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

# Cập nhật URL database với mật khẩu của bạn
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.wteysnuvgzorqltfeqsg:hungjsgxsw6@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

# Tạo engine với các tham số phù hợp cho Supabase
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