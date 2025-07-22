```markdown
# Multi-Source News Aggregation System

Một hệ thống thu thập bài báo đa nguồn, cung cấp kho tin tức phong phú cho bạn đọc, tích hợp Machine Learning để phân loại nội dung dựa trên bộ dữ liệu hơn 5000 bài báo được gắn nhãn chuẩn. Hệ thống đồng thời hỗ trợ các chức năng dành riêng cho tác giả. Bộ dữ liệu được xây dựng bài bản bằng cách thu thập bài viết theo từng danh mục cụ thể, đảm bảo chất lượng huấn luyện.

---

## 🔹 Cấu trúc Dự án

- `main.py`: Tập tin FastAPI khởi tạo `app`.
- `app/`: Xử lý Authentication, Database, Models, Schemas, Utils.
- `data_scraping/`: Các mô-đun scrape tin tức từ nhiều nguồn báo lớn.
- `ux/`: Giao diện Templates HTML và tài nguyên tĩnh (CSS/JS).
- `requirements.txt`: Danh sách thư viện Python cần cài đặt.
- `NaiveBayes-NLP.py`: Mô hình Machine Learning phân loại nội dung tin tức.
- `Dockerfile`: Đóng gói project thành Docker Image để deploy.

---

## 🔹 Cài Đặt Local Phát Triển

1. **Clone Repository**:
```bash
git clone https://github.com/nguyenvphihung/Multi-Source-News-Aggregation-System.git
cd Multi-Source-News-Aggregation-System
```

2. **Tạo môi trường ảo (khuyến khích)**:
```bash
python -m venv venv
source venv/bin/activate    # Hoặc venv\Scripts\activate (Windows)
```

3. **Cài đặt thư viện**:
```bash
pip install -r requirements.txt

## 🤖 Setup PhoBERT Model

The PhoBERT toxic comment model is not included in Git due to file size (515MB).

**Option 1: Use your existing model**
```bash
# Copy your model to project directory
cp -r /path/to/your/phobert_toxic_comment_model ./
```

**Option 2: Download from external source**
```bash
# Update download_model.py with actual URLs
python download_model.py
```

**Option 3: Skip AI moderation (fallback to Colab)**
The system will automatically fallback to Colab-based moderation if PhoBERT model is not found.
```

4. **Thiết lập biến môi trường**:
- Tạo file `.env` với nội dung mẫu:
```bash
DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database>
SECRET_KEY=your_secret_key_here
DEBUG=True
```
- Hoặc thiết lập trực tiếp environment variables nếu deploy cloud.

5. **Chạy server local**:
```bash
python -m uvicorn main:app --reload --timeout-graceful-shutdown 1
```
Truy cập: `http://127.0.0.1:8000`

---

## 🔹 Database

- Sử dụng **Supabase** (PostgreSQL Cloud Database).
- Các bảng dữ liệu chính:
  - `Articles`
  - `Users`
  - `Settings`
- ORM: SQLAlchemy (`app/models.py`)

---

## 🔹 Ghi chú thêm

- Backend render HTML trực tiếp (không phải Single Page Application - SPA).
- Phân loại nội dung bài báo bằng Machine Learning (Naive Bayes Classifier).
- Quá trình scraping được ghi log chi tiết.
- Dockerfile hỗ trợ build và deploy container.

---

## 🔹 Liên hệ
Email: nguyenvanphihung24@gmail.com