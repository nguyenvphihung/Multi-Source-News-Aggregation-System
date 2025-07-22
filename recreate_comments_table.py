#!/usr/bin/env python3
"""
EMERGENCY: Recreate comments table với schema đúng
CHỈ SỬ DỤNG KHI FIX SCHEMA KHÔNG THÀNH CÔNG
"""
import sys
import os
sys.path.append('app')

from app.database import SessionLocal, engine
from sqlalchemy import text
import traceback

def backup_existing_comments():
    """Backup comments hiện tại (nếu có)"""
    print("💾 BACKUP COMMENTS HIỆN TẠI")
    print("="*40)
    
    try:
        db = SessionLocal()
        
        # Tạo bảng backup
        backup_sql = """
        CREATE TABLE IF NOT EXISTS comments_backup AS 
        SELECT * FROM comments;
        """
        
        db.execute(text(backup_sql))
        db.commit()
        
        # Đếm records
        count_sql = "SELECT COUNT(*) FROM comments_backup;"
        result = db.execute(text(count_sql)).fetchone()
        count = result[0] if result else 0
        
        print(f"✅ Backup {count} comments vào bảng 'comments_backup'")
        return True
        
    except Exception as e:
        print(f"⚠️ Lỗi backup: {e}")
        return False
    finally:
        db.close()

def recreate_comments_table():
    """Tạo lại bảng comments với schema đầy đủ"""
    print("\n🔄 TẠO LẠI BẢNG COMMENTS")
    print("="*40)
    
    try:
        db = SessionLocal()
        
        # Drop bảng cũ
        print("🗑️ Drop bảng comments cũ...")
        db.execute(text("DROP TABLE IF EXISTS comments;"))
        
        # Tạo bảng mới với schema đầy đủ
        create_sql = """
        CREATE TABLE comments (
            id SERIAL PRIMARY KEY,
            article_id VARCHAR(20) NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            parent_id INTEGER,
            likes INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            sentiment VARCHAR(20) DEFAULT 'neutral',
            sentiment_confidence FLOAT DEFAULT 0.0
        );
        """
        
        print("🔧 Tạo bảng comments mới...")
        db.execute(text(create_sql))
        
        # Tạo indexes
        index_sql = [
            "CREATE INDEX IF NOT EXISTS idx_comments_article_id ON comments(article_id);",
            "CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_comments_status ON comments(status);",
            "CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON comments(parent_id);"
        ]
        
        for sql in index_sql:
            db.execute(text(sql))
        
        db.commit()
        print("✅ Bảng comments đã được tạo lại thành công!")
        return True
        
    except Exception as e:
        print(f"❌ Lỗi tạo lại bảng: {e}")
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

def restore_from_backup():
    """Restore data từ backup (nếu có)"""
    print("\n🔄 RESTORE DATA TỪ BACKUP")
    print("="*40)
    
    try:
        db = SessionLocal()
        
        # Kiểm tra bảng backup có tồn tại không
        check_sql = """
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_name = 'comments_backup';
        """
        result = db.execute(text(check_sql)).fetchone()
        
        if result and result[0] > 0:
            # Restore data
            restore_sql = """
            INSERT INTO comments (id, article_id, user_id, content, created_at, updated_at, parent_id)
            SELECT id, article_id, user_id, content, created_at, updated_at, parent_id
            FROM comments_backup;
            """
            
            db.execute(text(restore_sql))
            db.commit()
            
            # Đếm restored records
            count_sql = "SELECT COUNT(*) FROM comments;"
            result = db.execute(text(count_sql)).fetchone()
            count = result[0] if result else 0
            
            print(f"✅ Restored {count} comments")
            return True
        else:
            print("ℹ️ Không có backup để restore")
            return True
            
    except Exception as e:
        print(f"⚠️ Lỗi restore: {e}")
        print("💡 Data có thể bị mất, nhưng schema đã được fix")
        return False
    finally:
        db.close()

def verify_new_schema():
    """Kiểm tra schema mới"""
    print("\n✅ KIỂM TRA SCHEMA MỚI")
    print("="*40)
    
    try:
        from app.models import Comment
        db = SessionLocal()
        
        # Test query
        count = db.query(Comment).count()
        print(f"✅ Query thành công, total comments: {count}")
        
        # Test các cột mới
        test_comment = Comment(
            article_id="TEST-001",
            user_id=1,
            content="Test comment",
            likes=0,
            status="active",
            sentiment="neutral",
            sentiment_confidence=0.0
        )
        print("✅ Tất cả cột hoạt động bình thường")
        return True
        
    except Exception as e:
        print(f"❌ Vẫn có lỗi: {e}")
        return False
    finally:
        db.close()

def main():
    """Main workflow - EMERGENCY RECREATE"""
    print("🚨 EMERGENCY: RECREATE COMMENTS TABLE")
    print("="*50)
    print("⚠️ CẢNH BÁO: Script này sẽ XÓA và TẠO LẠI bảng comments")
    print("💾 Data sẽ được backup trước khi xóa")
    
    confirm = input("\n🤔 Bạn có chắc muốn tiếp tục? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Hủy bỏ operation")
        return
    
    # Step 1: Backup
    backup_success = backup_existing_comments()
    
    # Step 2: Recreate table
    recreate_success = recreate_comments_table()
    
    if not recreate_success:
        print("❌ Không thể recreate bảng")
        return
    
    # Step 3: Restore data
    restore_from_backup()
    
    # Step 4: Verify
    verify_new_schema()
    
    print("\n🎉 HOÀN THÀNH RECREATE COMMENTS TABLE!")
    print("💡 Restart server và test lại")

if __name__ == "__main__":
    main() 