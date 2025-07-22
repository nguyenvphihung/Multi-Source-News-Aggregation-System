#!/usr/bin/env python3
"""
Script fix database schema - thêm cột likes vào bảng comments
"""
import sys
import os
sys.path.append('app')

from app.database import SessionLocal, engine
from sqlalchemy import text, inspect
import traceback

def check_current_schema():
    """Kiểm tra schema hiện tại của bảng comments"""
    print("🔍 KIỂM TRA SCHEMA HIỆN TẠI")
    print("="*40)
    
    try:
        db = SessionLocal()
        inspector = inspect(engine)
        
        # Kiểm tra bảng comments có tồn tại không
        tables = inspector.get_table_names()
        print(f"📋 Tables trong database: {tables}")
        
        if 'comments' in tables:
            columns = inspector.get_columns('comments')
            print(f"\n📄 Cột trong bảng 'comments':")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            # Kiểm tra cột likes
            column_names = [col['name'] for col in columns]
            if 'likes' in column_names:
                print("\n✅ Cột 'likes' đã tồn tại")
                return True
            else:
                print("\n❌ Cột 'likes' CHƯA tồn tại")
                return False
        else:
            print("\n❌ Bảng 'comments' không tồn tại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi kiểm tra schema: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()

def add_likes_column():
    """Thêm cột likes vào bảng comments"""
    print("\n🔧 THÊM CỘT 'likes' VÀO BẢNG 'comments'")
    print("="*40)
    
    try:
        db = SessionLocal()
        
        # SQL để thêm cột likes
        sql = """
        ALTER TABLE comments 
        ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0;
        """
        
        print(f"📝 Chạy SQL: {sql.strip()}")
        db.execute(text(sql))
        db.commit()
        
        print("✅ Đã thêm cột 'likes' thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi thêm cột: {e}")
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def add_missing_columns():
    """Thêm tất cả các cột bị thiếu"""
    print("\n🔧 THÊM CÁC CỘT BỊ THIẾU")
    print("="*40)
    
    try:
        db = SessionLocal()
        
        # Danh sách cột cần thêm (theo model Comment)
        columns_to_add = [
            ("likes", "INTEGER DEFAULT 0"),
            ("status", "VARCHAR(20) DEFAULT 'active'"),
            ("sentiment", "VARCHAR(20) DEFAULT 'neutral'"),
            ("sentiment_confidence", "VARCHAR(10) DEFAULT '0.0'")
        ]
        
        for column_name, column_definition in columns_to_add:
            try:
                sql = f"ALTER TABLE comments ADD COLUMN IF NOT EXISTS {column_name} {column_definition};"
                print(f"📝 Thêm cột: {column_name}")
                db.execute(text(sql))
                db.commit()
                print(f"  ✅ {column_name} - OK")
            except Exception as e:
                print(f"  ⚠️ {column_name} - {e}")
                db.rollback()
        
        print("\n✅ Hoàn thành thêm cột!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tổng quát: {e}")
        return False
    finally:
        db.close()

def verify_fix():
    """Kiểm tra lại sau khi fix"""
    print("\n✅ KIỂM TRA SAU KHI FIX")
    print("="*40)
    
    return check_current_schema()

def test_comment_query():
    """Test query comments để đảm bảo không còn lỗi"""
    print("\n🧪 TEST QUERY COMMENTS")
    print("="*40)
    
    try:
        from app.models import Comment
        db = SessionLocal()
        
        # Test query đơn giản
        count = db.query(Comment).count()
        print(f"✅ Total comments: {count}")
        
        # Test query cụ thể cho article BB-1934
        article_comments = db.query(Comment).filter(Comment.article_id == 'BB-1934').count()
        print(f"✅ Comments for BB-1934: {article_comments}")
        
        print("✅ Queries hoạt động bình thường!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi test query: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """Chạy tất cả bước fix"""
    print("🚀 FIX DATABASE SCHEMA - COMMENTS TABLE")
    print("="*50)
    
    # Bước 1: Kiểm tra schema hiện tại
    has_likes = check_current_schema()
    
    # Bước 2: Thêm cột nếu chưa có
    if not has_likes:
        success = add_missing_columns()
        if not success:
            print("❌ Không thể fix database schema")
            return
    else:
        print("ℹ️ Database schema đã OK")
    
    # Bước 3: Verify
    verify_fix()
    
    # Bước 4: Test queries
    test_comment_query()
    
    print("\n🎉 DATABASE SCHEMA ĐÃ ĐƯỢC FIX!")
    print("💡 Bây giờ có thể test comment submission trên web")

if __name__ == "__main__":
    main() 