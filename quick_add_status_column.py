#!/usr/bin/env python3
"""
QUICK FIX: Chỉ thêm cột status vào bảng comments
"""
import sys
import os
sys.path.append('app')

def quick_fix():
    """Quick fix chỉ thêm cột status"""
    print("⚡ QUICK FIX: Thêm cột STATUS")
    print("="*30)
    
    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        
        db = SessionLocal()
        
        # Thêm cột status
        sql = "ALTER TABLE comments ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';"
        print(f"📝 SQL: {sql}")
        
        db.execute(text(sql))
        db.commit()
        
        print("✅ Cột STATUS đã được thêm!")
        
        # Test query
        test_sql = "SELECT column_name FROM information_schema.columns WHERE table_name = 'comments' AND column_name = 'status';"
        result = db.execute(text(test_sql)).fetchone()
        
        if result:
            print("✅ Verify: Cột STATUS tồn tại trong database")
        else:
            print("❌ Verify: Cột STATUS chưa được tạo")
            
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    quick_fix()
    print("\n💡 Bây giờ restart server và test lại!")
    print("   python -m uvicorn main:app --reload") 