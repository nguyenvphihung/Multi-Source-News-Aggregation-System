#!/usr/bin/env python3
"""
🔍 TEST COMMENT DATABASE
=======================
Kiểm tra xem comment có được lưu và query đúng không
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.database import get_db
from app.models import Comment, User, Article
from sqlalchemy.orm import Session

def test_comments_in_database():
    """Test comments trong database"""
    print("🔍 KIỂM TRA COMMENTS TRONG DATABASE")
    print("="*50)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Test article exists
        article = db.query(Article).filter(Article.article_id == "BB-1934").first()
        if article:
            print(f"✅ Article BB-1934 tồn tại: {article.title[:50]}...")
        else:
            print("❌ Article BB-1934 không tồn tại")
            return
        
        # Test users
        users = db.query(User).all()
        print(f"📊 Total users: {len(users)}")
        for user in users[:3]:  # Show first 3 users
            print(f"   User {user.id}: {user.first_name} {user.last_name} ({user.email})")
        
        # Test all comments
        all_comments = db.query(Comment).all()
        print(f"📊 Total comments: {len(all_comments)}")
        
        # Test comments for BB-1934
        bb_comments = db.query(Comment).filter(Comment.article_id == "BB-1934").all()
        print(f"📊 Comments cho BB-1934: {len(bb_comments)}")
        
        for comment in bb_comments:
            user = db.query(User).filter(User.id == comment.user_id).first()
            user_name = f"{user.first_name} {user.last_name}" if user else f"User ID {comment.user_id} (NOT FOUND)"
            
            print(f"   Comment {comment.id}:")
            print(f"     Content: {comment.content[:50]}...")
            print(f"     User: {user_name}")
            print(f"     Status: {comment.status}")
            print(f"     Parent ID: {comment.parent_id}")
            print(f"     Created: {comment.created_at}")
            print(f"     Likes: {comment.likes}")
            if hasattr(comment, 'sentiment'):
                print(f"     Sentiment: {comment.sentiment}")
            print()
        
        # Test query như trong template
        print("🔍 TEST QUERY NHƯ TRONG TEMPLATE")
        print("="*50)
        
        template_comments = db.query(Comment).filter(
            Comment.article_id == "BB-1934",
            Comment.parent_id == None,  # Chỉ lấy bình luận gốc
            Comment.status == "active"
        ).order_by(Comment.created_at.desc()).all()
        
        print(f"📊 Comments theo template query: {len(template_comments)}")
        
        for comment in template_comments:
            user = db.query(User).filter(User.id == comment.user_id).first()
            print(f"   Template Comment {comment.id}: {comment.content[:30]}... by {user.first_name if user else 'Unknown'}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    finally:
        db.close()

def test_create_dummy_user():
    """Tạo dummy user nếu user_id = 1 không tồn tại"""
    print("\n🛠️ KIỂM TRA VÀ TẠO DUMMY USER")
    print("="*50)
    
    db = next(get_db())
    
    try:
        # Check if user_id = 1 exists
        user1 = db.query(User).filter(User.id == 1).first()
        
        if user1:
            print(f"✅ User ID 1 đã tồn tại: {user1.first_name} {user1.last_name}")
        else:
            print("❌ User ID 1 không tồn tại, tạo dummy user...")
            
            # Create dummy user
            dummy_user = User(
                id=1,
                first_name="Test",
                last_name="User",
                email="test@example.com",
                phone="0123456789",
                password="dummy_password",
                role="User",
                status="Active"
            )
            
            db.add(dummy_user)
            db.commit()
            print("✅ Đã tạo dummy user ID 1")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
    
    finally:
        db.close()

def main():
    print("🔍 TEST COMMENT DATABASE & DISPLAY")
    print("="*50)
    
    # Test 1: Create dummy user if needed
    test_create_dummy_user()
    
    # Test 2: Check comments in database
    test_comments_in_database()
    
    print("\n💡 RECOMMENDATIONS:")
    print("="*50)
    print("1. Nếu có comments nhưng user NOT FOUND → Tạo dummy users")
    print("2. Nếu có comments nhưng template query = 0 → Check status/parent_id")
    print("3. Nếu không có comments cho BB-1934 → Test submit comment")

if __name__ == "__main__":
    main() 