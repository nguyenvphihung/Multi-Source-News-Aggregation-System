import sys
import os

# Thêm thư mục gốc vào đường dẫn để import các module từ app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Comment, Article
import pandas as pd
from sqlalchemy.orm import joinedload
import re
from datetime import datetime

def clean_text(text):
    """Làm sạch văn bản bình luận"""
    if not text:
        return ""
    # Loại bỏ HTML tags
    text = re.sub(r'<.*?>', '', text)
    # Loại bỏ ký tự đặc biệt và số
    text = re.sub(r'[^\w\s]', '', text)
    # Chuyển về chữ thường
    text = text.lower()
    return text.strip()

def collect_comments(output_file="comment_data.csv"):
    """Thu thập dữ liệu bình luận từ cơ sở dữ liệu"""
    db = SessionLocal()
    try:
        # Lấy tất cả bình luận
        comments = db.query(Comment).all()
        
        # Tạo dictionary để map article_id với article info
        articles = db.query(Article).all()
        article_dict = {article.article_id: article for article in articles}
        
        data = []
        for comment in comments:
            # Lấy thông tin article từ dictionary
            article = article_dict.get(comment.article_id)
            
            # Thu thập thông tin bình luận (chỉ những cột có tồn tại)
            comment_data = {
                "id": comment.id,
                "content": comment.content,
                "cleaned_content": clean_text(comment.content),
                "user_id": comment.user_id,
                "article_id": comment.article_id,
                "article_title": article.title if article else None,
                "article_type": article.type if article else None,
                "is_reply": comment.parent_id is not None if hasattr(comment, 'parent_id') else False,
                "parent_id": comment.parent_id if hasattr(comment, 'parent_id') else None,
                "created_at": comment.created_at,
                "timestamp": int(datetime.timestamp(comment.created_at)) if comment.created_at else None
            }
            data.append(comment_data)
        
        # Tạo DataFrame và lưu vào file CSV
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"Đã thu thập {len(data)} bình luận và lưu vào {output_file}")
        
        # Hiển thị một số thống kê cơ bản
        print(f"Số lượng bình luận gốc: {len(df[df['is_reply'] == False])}")
        print(f"Số lượng phản hồi: {len(df[df['is_reply'] == True])}")
        
        return df
    
    finally:
        db.close()

if __name__ == "__main__":
    collect_comments() 