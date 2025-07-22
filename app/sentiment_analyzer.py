"""
Module phân tích sentiment cho bình luận
Tích hợp model ML đã train vào hệ thống
"""
import os
import re
import joblib
import pandas as pd
from pathlib import Path

class SentimentAnalyzer:
    """Class để phân tích sentiment của bình luận"""
    
    def __init__(self, model_dir="models"):
        """
        Khởi tạo analyzer với đường dẫn đến model
        
        Args:
            model_dir (str): Thư mục chứa model files
        """
        self.model_dir = Path(model_dir)
        self.model = None
        self.vectorizer = None
        self.is_loaded = False
        
        # Thử load model ngay khi khởi tạo
        self.load_model()
    
    def load_model(self):
        """Load model và vectorizer từ file"""
        try:
            model_path = self.model_dir / "sentiment_model.pkl"
            vectorizer_path = self.model_dir / "vectorizer.pkl"
            
            if model_path.exists() and vectorizer_path.exists():
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.is_loaded = True
                print("✅ Model sentiment đã được load thành công!")
            else:
                print("⚠️ Không tìm thấy model files. Sentiment analysis sẽ không khả dụng.")
                print(f"   Tìm kiếm tại: {model_path}")
                print(f"   Tìm kiếm tại: {vectorizer_path}")
                self.is_loaded = False
                
        except Exception as e:
            print(f"❌ Lỗi khi load model: {e}")
            self.is_loaded = False
    
    def preprocess_text(self, text):
        """
        Tiền xử lý văn bản trước khi phân tích
        
        Args:
            text (str): Văn bản cần xử lý
            
        Returns:
            str: Văn bản đã được xử lý
        """
        if pd.isna(text) or not text:
            return ""
        
        text = str(text)
        
        # 1. Loại bỏ URL
        text = re.sub(r'http\S+|www\S+|https\S+', ' ', text, flags=re.MULTILINE)
        
        # 2. Loại bỏ emoji
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r' ', text)
        
        # 3. Đưa về chữ thường
        text = text.lower()
        
        # 4. Chuẩn hóa các ký tự lặp lại
        text = re.sub(r'(.)\1+', r'\1', text)
        
        # 5. Chỉ giữ lại chữ cái tiếng Việt và khoảng trắng
        text = re.sub(r'[^a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
        
        # 6. Xử lý khoảng trắng thừa
        text = ' '.join(text.split())
        
        return text
    
    def predict_sentiment(self, text):
        """
        Dự đoán sentiment của một đoạn text
        
        Args:
            text (str): Văn bản cần phân tích
            
        Returns:
            dict: Kết quả phân tích với sentiment và confidence
        """
        if not self.is_loaded:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "error": "Model chưa được load"
            }
        
        try:
            # Tiền xử lý
            processed_text = self.preprocess_text(text)
            
            if not processed_text.strip():
                return {
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "note": "Text rỗng sau khi xử lý"
                }
            
            # Vectorize
            vectorized = self.vectorizer.transform([processed_text])
            
            # Dự đoán
            prediction = self.model.predict(vectorized)[0]
            probabilities = self.model.predict_proba(vectorized)[0]
            confidence = max(probabilities)
            
            return {
                "sentiment": prediction,
                "confidence": float(confidence),
                "processed_text": processed_text[:100] + "..." if len(processed_text) > 100 else processed_text
            }
            
        except Exception as e:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "error": f"Lỗi khi phân tích: {str(e)}"
            }
    
    def predict_batch(self, texts):
        """
        Dự đoán sentiment cho nhiều văn bản cùng lúc
        
        Args:
            texts (list): Danh sách các văn bản
            
        Returns:
            list: Danh sách kết quả phân tích
        """
        results = []
        for text in texts:
            results.append(self.predict_sentiment(text))
        return results
    
    def get_sentiment_stats(self, comments):
        """
        Thống kê sentiment từ danh sách bình luận
        
        Args:
            comments (list): Danh sách bình luận
            
        Returns:
            dict: Thống kê phân bố sentiment
        """
        if not comments:
            return {"positive": 0, "negative": 0, "neutral": 0}
        
        sentiments = []
        for comment in comments:
            result = self.predict_sentiment(comment)
            sentiments.append(result["sentiment"])
        
        # Đếm phân bố
        stats = {
            "positive": sentiments.count("positive"),
            "negative": sentiments.count("negative"), 
            "neutral": sentiments.count("neutral"),
            "total": len(sentiments)
        }
        
        # Tính phần trăm
        if stats["total"] > 0:
            for key in ["positive", "negative", "neutral"]:
                stats[f"{key}_percent"] = round(stats[key] / stats["total"] * 100, 1)
        
        return stats

# Tạo instance global để sử dụng trong toàn bộ app
sentiment_analyzer = SentimentAnalyzer()

def analyze_comment_sentiment(text):
    """
    Hàm helper để phân tích sentiment của một bình luận
    
    Args:
        text (str): Nội dung bình luận
        
    Returns:
        dict: Kết quả phân tích sentiment
    """
    return sentiment_analyzer.predict_sentiment(text)

def get_comment_stats(comments):
    """
    Hàm helper để lấy thống kê sentiment của danh sách bình luận
    
    Args:
        comments (list): Danh sách nội dung bình luận
        
    Returns:
        dict: Thống kê phân bố sentiment
    """
    return sentiment_analyzer.get_sentiment_stats(comments) 