# Giải Thích Cấu Trúc PhoBERT Model

## 📁 Folder: `phobert_toxic_comment_model/`

Đây là một **PhoBERT model đã được fine-tune** để phân loại bình luận độc hại tiếng Việt.

## 📄 Phân Tích Từng File:

### 🧠 **Core Model Files:**

#### 1. `model.safetensors` (515MB)
- **Chức năng**: Chứa trọng số (weights) của neural network
- **Định dạng**: SafeTensors (an toàn hơn pickle)
- **Kích thước**: 515MB → Model lớn, chất lượng cao
- **Vai trò**: Trái tim của model, chứa kiến thức đã học

#### 2. `config.json` (881B)
- **Chức năng**: Cấu hình kiến trúc model
- **Nội dung**: 
  - Số layers, attention heads
  - Hidden size, vocab size
  - Label mapping (0,1,2)
- **Vai trò**: "Bản thiết kế" của model

### 🔤 **Tokenization Files:**

#### 3. `vocab.txt` (874KB, 63,997 lines)
- **Chức năng**: Từ điển của model
- **Nội dung**: 63,997 từ/token tiếng Việt
- **Vai trò**: Chuyển đổi text → numbers mà model hiểu được

#### 4. `bpe.codes` (1.1MB)
- **Chức năng**: Byte Pair Encoding rules
- **Vai trò**: Chia nhỏ từ thành sub-words (xử lý từ mới)
- **Ví dụ**: "xin chào" → ["x", "in", "ch", "ào"]

#### 5. `tokenizer_config.json` (1.2KB)
- **Chức năng**: Cấu hình tokenizer
- **Nội dung**: Các token đặc biệt (`<s>`, `</s>`, `<pad>`, `<mask>`)
- **Vai trò**: Hướng dẫn cách xử lý text input

#### 6. `special_tokens_map.json` (167B)
- **Chức năng**: Mapping token đặc biệt
- **Nội dung**: 
  - `<s>`: Bắt đầu câu
  - `</s>`: Kết thúc câu  
  - `<pad>`: Padding token
  - `<mask>`: Masked token

#### 7. `added_tokens.json` (22B)
- **Chức năng**: Token được thêm vào sau khi train
- **Kích thước nhỏ**: Chỉ 4 dòng → ít token mới

### ⚙️ **Training Files:**

#### 8. `training_args.bin` (5.2KB)
- **Chức năng**: Lưu tham số training
- **Nội dung**: Learning rate, batch size, epochs, v.v.
- **Vai trò**: Thông tin về cách model được train

## 🏗️ **Kiến Trúc Model:**

```
Input Text (Tiếng Việt)
    ↓
Tokenizer (vocab.txt + bpe.codes)
    ↓
Token IDs
    ↓
PhoBERT Layers (model.safetensors)
    ↓
Classification Head
    ↓
Output: Label 0/1/2 + Confidence
```

## 🎯 **Mục Đích Sử Dụng:**

### ✅ **Hoạt động tự động:**
1. **Input**: "dm thằng nào viết bài này"
2. **Tokenization**: Chuyển thành token IDs
3. **Model prediction**: PhoBERT xử lý
4. **Output**: Label 2 (độc hại) với confidence 0.95

### 📊 **Label Meanings:**
- **Label 0**: "Bài viết hay quá!" → An toàn
- **Label 1**: "Không đồng ý" → Tiêu cực nhẹ  
- **Label 2**: "dm, ngu vl" → Độc hại

## 💡 **So Sánh Kích Thước:**

| File | Kích thước | % Total | Vai trò |
|------|------------|---------|---------|
| `model.safetensors` | 515MB | ~97% | Model weights |
| `vocab.txt` | 874KB | ~1.6% | Vocabulary |
| `bpe.codes` | 1.1MB | ~2% | Tokenization |
| Còn lại | <10KB | <0.1% | Config |

## 🚀 **Ưu điểm của PhoBERT:**

1. **Tiếng Việt native**: Hiểu grammar, context Việt Nam
2. **Pre-trained**: Đã học từ massive Vietnamese corpus  
3. **Fine-tuned**: Được train đặc biệt cho toxic detection
4. **BERT architecture**: State-of-the-art NLP model

## ⚡ **Performance:**

- **Model size**: ~530MB total
- **Vocabulary**: 63,997 tokens (rất lớn)
- **Architecture**: RoBERTa-based (improved BERT)
- **Language**: Vietnamese specialized
- **Task**: Sequence classification (3 classes)

## 🔧 **Yêu Cầu Hệ Thống:**

- **RAM**: Tối thiểu 2GB cho model inference
- **Storage**: 530MB disk space
- **Dependencies**: PyTorch + Transformers
- **CPU/GPU**: CPU đủ, GPU tốt hơn (nếu có)

---

**🎉 Đây là một model AI chất lượng cao, được train chuyên biệt cho việc kiểm duyệt bình luận tiếng Việt!** 