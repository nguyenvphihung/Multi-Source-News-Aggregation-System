from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
import urllib


SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://@ADMIN-PC/dataBao?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
# SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://@MSI\\SQLEXPRESS/dataBao?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
# SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://ad:nckh123%40@nckh.database.windows.net/dataBao?driver=ODBC+Driver+17+for+SQL+Server"


engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"timeout": 5})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Hàm kết nối CSDL
def get_db():
    db = None
    try:
        db = SessionLocal()
        yield db
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Lỗi kết nối database")
    finally:
        if db:
            db.close()