import os
import traceback
from dotenv import load_dotenv

def test_db_connection():
    try:
        print("1. Loading .env file...")
        load_dotenv()
        
        print("2. Getting DATABASE_URL...")
        db_url = os.getenv("DATABASE_URL")
        print(f"   DATABASE_URL: {db_url[:50]}..." if db_url else "   DATABASE_URL: None")
        
        if not db_url:
            print("❌ ERROR: DATABASE_URL not found in environment")
            return False
            
        print("3. Testing SQLAlchemy import...")
        from sqlalchemy import create_engine
        
        print("4. Creating engine...")
        engine = create_engine(db_url, connect_args={"connect_timeout": 5})
        
        print("5. Testing connection...")
        with engine.connect() as conn:
            print("6. Running test query...")
            result = conn.execute("SELECT 1")
            print(f"   Query result: {result.fetchone()}")
            
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    test_db_connection() 