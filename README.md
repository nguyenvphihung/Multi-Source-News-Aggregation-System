## Cấu trúc dự án

- `main.py`: Tập tin chính chứa mã nguồn FastAPI với các endpoint để lấy dữ liệu và hiển thị giao diện.
- `app/models.py`: Chứa các mô hình dữ liệu (models) cho SQLAlchemy.
- `app/database.py`: Thiết lập kết nối cơ sở dữ liệu với SQLAlchemy.
- `app/schhemas.py`: định nghĩa các lớp dữ liệu bằng cách sử dụng Pydantic, mô tả cấu trúc dữ liệu được gửi đến hoặc trả về từ API
- `Templates/`: Chứa các template HTML cho trang chủ, trang danh mục, và trang chi tiết bài viết.
- `static/`: Chứa các tài nguyên tĩnh : CSS,...

## Hướng dẫn Cài đặt

1. **Clone** dự án từ GitHub:
   ```bash
   git clone <URL_REPOSITORY>
   cd <TÊN_THƯ_MỤC_DỰ_ÁN>
   ```

2. **Cài đặt các thư viện phụ thuộc:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình cơ sở dữ liệu**:
   - Thiết lập kết nối đến cơ sở dữ liệu trong `app/database.py` theo cấu hình riêng.

4. **Chạy ứng dụng**:
   ```bash
   uvicorn main:app --reload
   ```

## Cấu trúc CSDL (Database)

Bảng chính trong CSDL:

- **Article**:
  - `article_id`: Mã định danh duy nhất của bài báo.
  - `title`: Tiêu đề bài báo.
  - `description`: Mô tả ngắn gọn.
  - `content`: Nội dung chi tiết của bài báo.
  - `date_posted`: Ngày đăng.
  - `author`: Tác giả bài báo.
  - `source_url`: Đường dẫn gốc của bài báo.
  - `status`: Trạng thái bài báo.
  - `type`: Loại/danh mục bài báo.
  - `image_urls`: Danh sách URL ảnh liên quan.
  - `video_urls`: Danh sách URL video liên quan.

## Hướng Dẫn Sử Dụng
- Tạo database dataBaoViet và table Articles, Users, Settings trong SQLServer trước khi chạy file main.py
- Cú pháp tạo table:
```bash
use dataBao

-- Tạo bảng Articles
CREATE TABLE Articles (
    article_id VARCHAR(20) PRIMARY KEY,
    title NVARCHAR(255) NOT NULL,
    description NVARCHAR(MAX) NULL,
    content NVARCHAR(MAX) NULL,
    date_posted DATETIME NULL,
    author NVARCHAR(100) NULL,
    source_url NVARCHAR(255) NULL,
    status NVARCHAR(50) NULL,
    type NVARCHAR(50) NULL,
    image_urls NVARCHAR(MAX) NULL,
    video_urls NVARCHAR(MAX) NULL
);

-- Tạo bảng Users
CREATE TABLE Users (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    FirstName NVARCHAR(255) NOT NULL,
    LastName NVARCHAR(255) NOT NULL,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    Phone NVARCHAR(20) NULL UNIQUE,
    Password NVARCHAR(255) NOT NULL,
    Newsletter BIT DEFAULT 0,
    TermsAccepted BIT DEFAULT 0,
    Role NVARCHAR(50) DEFAULT 'User',
    Status NVARCHAR(50) DEFAULT 'Active',
    RegistrationDate DATETIME DEFAULT GETDATE(),
    AvatarUrl NVARCHAR(255) NULL,
    author_requested BIT DEFAULT 0
);

-- Tạo bảng settings
CREATE TABLE settings (
    setting_key NVARCHAR(255) PRIMARY KEY,
    value NVARCHAR(MAX) NULL
);
```
- Truy cập trang chủ tại ngay khi chạy chương trình và có thể chuyển sang giao diện phía admin nếu tài khoản đăng nhập là admin,...
- Chọn danh mục từ thanh bar để xem các bài viết theo từng danh mục.
- Chọn một bài viết để xem chi tiết.