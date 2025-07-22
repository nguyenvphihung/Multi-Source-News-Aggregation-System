# Hướng Dẫn Test Thủ Công Trên Web

## 🌐 Bước 1: Mở trang web
1. Khởi chạy server: `python -m uvicorn main:app --reload`
2. Mở trình duyệt: `http://localhost:8000`
3. Tìm một bài viết có ID như `BB-1846` để test

## 📝 Bước 2: Nhập bình luận test

### Bình luận tích cực (sẽ được phê duyệt):
- "Bài viết rất hay và bổ ích!"
- "Cảm ơn tác giả đã chia sẻ"
- "Thông tin rất hữu ích"

### Bình luận tiêu cực nhẹ (có thể được phê duyệt):
- "Mình không đồng ý với quan điểm này"
- "Bài viết chưa thuyết phục lắm"

### Bình luận độc hại (sẽ bị từ chối):
- "dm thằng nào viết bài này"
- "mày viết gì vậy, ngu vl"
- "Spam spam spam click here"

## 🔍 Bước 3: Quan sát kết quả

### Với PhoBERT Local (mặc định):
- **Phê duyệt ngay**: Alert "✅ Bình luận đã được phê duyệt và đăng thành công!" + reload trang
- **Từ chối ngay**: Alert "❌ Bình luận bị từ chối: [lý do]"

### Với Colab Workflow:
- **Chờ xử lý**: Alert "✅ Bình luận đã được gửi để kiểm duyệt"

## 📁 Bước 4: Kiểm tra files

### File `pending_comments/comment_mapping.json`:
```json
{
  "comment_id": {
    "content": "nội dung bình luận",
    "article_id": "BB-1846",
    "user_id": 1,
    "parent_id": null,
    "timestamp": "2025-01-XX...",
    "status": "approved" // hoặc "rejected" hoặc "pending"
  }
}
```

### File `pending_comments/comments_for_colab.csv`:
```csv
comment_id,free_text,timestamp
uuid-here,nội dung bình luận,2025-01-XX...
```

## 🔄 Bước 5: Chuyển đổi chế độ

### Chuyển sang Colab workflow:
```bash
curl -X POST http://localhost:8000/api/switch-moderation-mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "colab"}'
```

### Chuyển về PhoBERT local:
```bash
curl -X POST http://localhost:8000/api/switch-moderation-mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "local"}'
```

## 📊 Bước 6: Kiểm tra trạng thái hệ thống
```bash
curl http://localhost:8000/api/moderation-status
```

## 🎯 Mục tiêu test

✅ **Thành công** khi:
- Bình luận tích cực được phê duyệt tự động
- Bình luận độc hại bị từ chối tự động  
- Files `comment_mapping.json` và `comments_for_colab.csv` được cập nhật
- Có thể chuyển đổi giữa local/colab mode

❌ **Cần sửa** khi:
- Server báo lỗi PhoBERT model
- Tất cả comment đều pending (không xử lý tự động)
- Files không được tạo/cập nhật 