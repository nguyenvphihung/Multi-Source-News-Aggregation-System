"""
Script cho Google Colab để xử lý comment moderation
Upload file CSV từ server, chạy model prediction, gửi kết quả về
"""

import pandas as pd
import numpy as np
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import re
import time

# ============= CẤU HÌNH =============
SERVER_URL = "http://your-server.com"  # Thay bằng URL server thực của bạn
RESULTS_ENDPOINT = f"{SERVER_URL}/api/process-colab-results"

# ============= FUNCTIONS =============

def preprocess_text(text):
    """Tiền xử lý văn bản (giống như trên server)"""
    if pd.isna(text) or not text:
        return ""
    
    text = str(text)
    
    # Loại bỏ URL
    text = re.sub(r'http\S+|www\S+|https\S+', ' ', text, flags=re.MULTILINE)
    
    # Loại bỏ emoji
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
    
    # Đưa về chữ thường
    text = text.lower()
    
    # Chuẩn hóa các ký tự lặp lại
    text = re.sub(r'(.)\1+', r'\1', text)
    
    # Chỉ giữ lại chữ cái tiếng Việt và khoảng trắng
    text = re.sub(r'[^a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ\s]', ' ', text)
    
    # Xử lý khoảng trắng thừa
    text = ' '.join(text.split())
    
    return text

def create_simple_model():
    """Tạo model đơn giản để demo (thay bằng model thực của bạn)"""
    print("🔧 Tạo model demo...")
    
    # Dữ liệu training đơn giản
    training_data = [
        ("bài viết hay tuyệt vời cảm ơn", 0),  # positive
        ("nội dung bổ ích hữu ích", 0),        # positive
        ("tệ dở không hay chán", 1),           # negative  
        ("không thích phản đối", 1),           # negative
        ("spam quảng cáo link", 2),            # toxic/spam
        ("chửi bậy xúc phạm", 2),             # toxic/spam
        ("ok bình thường", 0),                 # neutral -> positive
        ("không có gì đặc biệt", 1),          # neutral -> negative
    ]
    
    texts = [preprocess_text(text) for text, _ in training_data]
    labels = [label for _, label in training_data]
    
    # Train model
    vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)
    
    model = LogisticRegression(max_iter=1000)
    model.fit(X, labels)
    
    return model, vectorizer

def predict_comments(df, model, vectorizer):
    """Dự đoán label cho từng comment"""
    print(f"🔮 Đang dự đoán {len(df)} bình luận...")
    
    results = []
    
    for idx, row in df.iterrows():
        comment_id = row['comment_id']
        content = row['content']
        
        # Tiền xử lý
        processed_text = preprocess_text(content)
        
        if not processed_text.strip():
            # Text rỗng -> label 2 (filter out)
            label = 2
        else:
            # Predict với model
            vectorized = vectorizer.transform([processed_text])
            label = model.predict(vectorized)[0]
        
        results.append({
            "comment_id": comment_id,
            "label": int(label)
        })
        
        print(f"  {idx+1}/{len(df)}: '{content[:50]}...' → Label {label}")
    
    return results

def send_results_to_server(results):
    """Gửi kết quả về server"""
    print(f"📤 Đang gửi {len(results)} kết quả về server...")
    
    payload = {
        "results": results
    }
    
    try:
        response = requests.post(
            RESULTS_ENDPOINT,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Gửi kết quả thành công!")
                stats = result.get("stats", {})
                print(f"📊 Thống kê:")
                print(f"   - Đã xử lý: {stats.get('total_processed', 0)}")
                print(f"   - Lưu vào DB: {stats.get('saved_to_db', 0)}")
                print(f"   - Đã xóa: {stats.get('deleted', 0)}")
                print(f"   - Lỗi: {stats.get('errors', 0)}")
                return True
            else:
                print(f"❌ Server trả về lỗi: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi khi gửi request: {e}")
        return False

# ============= MAIN WORKFLOW =============

def main():
    """Workflow chính"""
    print("🚀 BẮT ĐẦU COMMENT MODERATION WORKFLOW")
    print("="*60)
    
    # Bước 1: Đọc file CSV đã upload
    print("📂 Bước 1: Đọc file CSV...")
    
    # Upload file comments_for_colab.csv từ server lên Colab trước khi chạy
    csv_file = "comments_for_colab.csv"
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        print(f"✅ Đọc thành công {len(df)} bình luận")
        print("📋 5 dòng đầu:")
        print(df.head())
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file {csv_file}")
        print("💡 Hãy upload file từ server lên Colab trước!")
        return
    except Exception as e:
        print(f"❌ Lỗi đọc file: {e}")
        return
    
    if len(df) == 0:
        print("⚠️ File CSV rỗng, không có gì để xử lý")
        return
    
    # Bước 2: Tạo/Load model
    print("\n🤖 Bước 2: Chuẩn bị model...")
    
    # Option A: Sử dụng model đã train sẵn (khuyến nghị)
    try:
        import joblib
        model = joblib.load('sentiment_model.pkl')
        vectorizer = joblib.load('vectorizer.pkl')
        print("✅ Load model đã train thành công!")
    except:
        print("⚠️ Không tìm thấy model đã train, sử dụng model demo...")
        model, vectorizer = create_simple_model()
    
    # Bước 3: Predict
    print("\n🔮 Bước 3: Dự đoán labels...")
    results = predict_comments(df, model, vectorizer)
    
    # Bước 4: Gửi kết quả về server
    print("\n📤 Bước 4: Gửi kết quả về server...")
    
    # Kiểm tra SERVER_URL
    if "your-server.com" in SERVER_URL:
        print("⚠️ CẢNH BÁO: Bạn cần thay đổi SERVER_URL ở đầu script!")
        print("💡 Ví dụ: SERVER_URL = 'http://localhost:8000'")
        print("\n🔍 Kết quả dự đoán (demo):")
        for result in results[:10]:  # Hiển thị 10 kết quả đầu
            print(f"  {result['comment_id']}: Label {result['label']}")
        return
    
    success = send_results_to_server(results)
    
    if success:
        print("\n🎉 HOÀN THÀNH! Workflow đã chạy thành công!")
    else:
        print("\n❌ Có lỗi xảy ra khi gửi kết quả. Kiểm tra lại SERVER_URL và kết nối mạng.")

# ============= SCRIPT CHẠY CHO COLAB =============

if __name__ == "__main__":
    # Chạy workflow
    main()

# ============= HƯỚNG DẪN SỬ DỤNG =============
"""
HƯỚNG DẪN CHẠY TRÊN GOOGLE COLAB:

1. CẤU HÌNH:
   - Thay đổi SERVER_URL thành URL thực của server (ví dụ: http://localhost:8000 hoặc domain thực)

2. UPLOAD FILES:
   - Upload file 'comments_for_colab.csv' từ server lên Colab
   - (Tùy chọn) Upload model files: 'sentiment_model.pkl', 'vectorizer.pkl' nếu có

3. CHẠY SCRIPT:
   !python colab_moderation_script.py

4. KẾT QUẢ:
   - Script sẽ tự động gửi kết quả về server
   - Comments với label 0,1 sẽ được lưu vào database
   - Comments với label 2 sẽ bị xóa

5. LABELS:
   - Label 0: Positive/Acceptable comments
   - Label 1: Negative but acceptable comments  
   - Label 2: Toxic/Spam comments (sẽ bị xóa)
""" 