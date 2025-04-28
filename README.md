# Multi-Source News Aggregation System

Một hệ thống thu thập bài báo đa nguồn, cung cấp kho tin tức phong phú cho bạn đọc, tích hợp Machine Learning để phân loại nội dung dựa trên bộ dữ liệu hơn 5000 bài báo được gắn nhãn chuẩn, đồng thời hỗ trợ các chức năng dành riêng cho tác giả. Bộ dữ liệu được xây dựng bài bản bằng cách thu thập bài viết theo từng danh mục cụ thể, đảm bảo chất lượng huấn luyện.

---

## 🔹 Cấu trúc Dự án

- `main.py`: Tập tin FastAPI chốt chứa `app`.
- `app/`: Xử lý Authentication, Database, Models, Schemas, Utils.
- `data_scraping/`: Mô-đun scrape tin tức từ các báo lớn: VnExpress, Dantri, VietnamPlus...
- `ux/`: Templates HTML và file tĩnh CSS/JS.
- `requirements.txt`: Danh sách thư viện Python cần cài.
- `NaiveBayes-NLP.py`: Mô hình phân loại tin tức.
- `Dockerfile`: Đóng gói project thành container Docker để deploy dễ dàng.

---

## 🔹 Cài Đặt Local Phát Triển

1. **Clone**:
```bash
git clone https://github.com/nguyenvphihung/Multi-Source-News-Aggregation-System.git
```

2. **Tạo môi trường ảo (tuỳ chọn)**:
```bash
python -m venv venv
source venv/bin/activate  # Hoặc venv\Scripts\activate (Windows)
```

3. **Cài thư viện**:
```bash
pip install -r requirements.txt
```

4. **Cấu hình biến môi trường**:
- Tạo biến môi trường trực tiếp hoặc tạo file `.env` theo mẫu:
```bash
DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database>
SECRET_KEY=your_secret_key_here
DEBUG=True
```

5. **Chạy server local**:
```bash
uvicorn main:app --reload
```

Truy cập: `http://127.0.0.1:8000`

---

## 🔹 Deploy bằng Docker

### Build Docker Image
```bash
docker build -t multi-source-news-aggregator .
```

### Run Docker Container
```bash
docker run -d -p 8000:10000 --env-file .env multi-source-news-aggregator
```

Truy cập: `http://localhost:8000`

**Ghi chú:** Nếu deploy trên Render.com ➔ không cần `.env`, chỉ cần set Environment Variables trong dashboard.

---

## 🔹 Database

- **Supabase** PostgreSQL Cloud
- Các bảng chính:
  - `Articles`
  - `Users`
  - `Settings`
- ORM sử dụng: SQLAlchemy (`app/models.py`)

---

## 🔹 Ghi Chú

- Backend render HTML trực tiếp (không phải SPA).
- Machine Learning phân loại nội dung: `NaiveBayes-NLP.py`, `text_classifier.pkl`.
- Quá trình scraping ghi log hoạt động.
- Có Dockerfile hỗ trợ deploy nhanh chóng.

---

## 🔹 Liên Hệ

Người phát triển: Nguyễn Văn Phi Hùng  
Email: nguyenvanphihung24