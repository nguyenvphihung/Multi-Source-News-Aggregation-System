"""
PhoBERT Service để phân loại bình luận độc hại
Tích hợp model PhoBERT đã train sẵn vào hệ thống
"""
import os
import re
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List, Optional
import logging

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoBERTService:
    """Service để phân loại bình luận độc hại bằng PhoBERT"""
    
    def __init__(self, model_path: str = "phobert_toxic_comment_model"):
        """
        Khởi tạo PhoBERT service
        
        Args:
            model_path (str): Đường dẫn đến thư mục chứa model PhoBERT
        """
        self.model_path = Path(model_path)
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        
        # Label mapping theo config.json của model
        self.id2label = {
            0: "LABEL_0",  # Bình luận tích cực/trung tính
            1: "LABEL_1",  # Bình luận tiêu cực nhẹ
            2: "LABEL_2"   # Bình luận độc hại/spam
        }
        
        self.label_descriptions = {
            0: "Bình luận tích cực/an toàn",
            1: "Bình luận tiêu cực nhẹ", 
            2: "Bình luận độc hại/spam"
        }
        
        # Tự động load model khi khởi tạo
        self.load_model()
    
    def load_model(self) -> bool:
        """
        Load tokenizer và model từ thư mục đã chỉ định
        
        Returns:
            bool: True nếu load thành công, False nếu có lỗi
        """
        try:
            if not self.model_path.exists():
                logger.error(f"❌ Không tìm thấy thư mục model: {self.model_path}")
                return False
            
            # Kiểm tra các file cần thiết
            required_files = ["config.json", "model.safetensors", "tokenizer_config.json"]
            for file in required_files:
                if not (self.model_path / file).exists():
                    logger.error(f"❌ Không tìm thấy file: {file}")
                    return False
            
            logger.info(f"🔄 Đang load PhoBERT model từ {self.model_path}...")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                trust_remote_code=True
            )
            
            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                trust_remote_code=True
            )
            
            # Chuyển model sang device phù hợp
            self.model.to(self.device)
            self.model.eval()  # Chế độ evaluation
            
            self.is_loaded = True
            logger.info(f"✅ PhoBERT model loaded thành công trên {self.device}")
            logger.info(f"📋 Model labels: {self.id2label}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi load PhoBERT model: {e}")
            self.is_loaded = False
            return False
    
    def preprocess_text(self, text: str) -> str:
        """
        Tiền xử lý văn bản trước khi đưa vào model
        
        Args:
            text (str): Văn bản gốc
            
        Returns:
            str: Văn bản đã được xử lý
        """
        if not text:
            return ""
        
        # Loại bỏ URL
        text = re.sub(r'http[s]?://\S+', ' ', text)
        text = re.sub(r'www\.\S+', ' ', text)
        
        # Loại bỏ email
        text = re.sub(r'\S+@\S+', ' ', text)
        
        # Loại bỏ số điện thoại (đơn giản)
        text = re.sub(r'\b\d{10,11}\b', ' ', text)
        
        # Loại bỏ ký tự đặc biệt thừa nhưng giữ dấu câu cơ bản
        text = re.sub(r'[^\w\s\.,!?]', ' ', text)
        
        # Chuẩn hóa khoảng trắng
        text = ' '.join(text.split())
        
        return text.strip()
    
    def predict_single(self, text: str) -> Dict:
        """
        Phân loại một bình luận đơn lẻ
        
        Args:
            text (str): Nội dung bình luận
            
        Returns:
            Dict: Kết quả phân loại với label, confidence, description, decision
        """
        if not self.is_loaded:
            return {
                "label": 2,  # Default reject nếu model không load được
                "confidence": 0.0,
                "description": "Model chưa được load",
                "decision": "reject",
                "reason": "PhoBERT model không khả dụng",
                "error": "PhoBERT model không khả dụng"
            }
        
        if not text or not text.strip():
            return {
                "label": 0,
                "confidence": 0.5,
                "description": "Văn bản trống",
                "processed_text": ""
            }
        
        try:
            # Tiền xử lý
            processed_text = self.preprocess_text(text)
            
            if not processed_text:
                return {
                    "label": 0,
                    "confidence": 0.5,
                    "description": "Văn bản trống sau xử lý",
                    "processed_text": ""
                }
            
            # Tokenize
            inputs = self.tokenizer(
                processed_text,
                return_tensors="pt",
                max_length=256,
                truncation=True,
                padding=True
            )
            
            # Chuyển inputs sang device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1)
                predicted_label = torch.argmax(logits, dim=-1).item()
                confidence = probabilities[0][predicted_label].item()
            
            # Decision logic theo toxic keywords + PhoBERT
            # Check for common Vietnamese toxic words first
            text_lower = processed_text.lower()
            toxic_keywords = ['đm', 'dm', 'đmm', 'dmm', 'vãi', 'shit', 'fuck', 
                             'con chó', 'thằng lol', 'mẹ kiếp', 'đồ ngu', 'óc chó']
            
            has_toxic_keyword = any(keyword in text_lower for keyword in toxic_keywords)
            
            if has_toxic_keyword:
                # Force reject if contains toxic keywords
                decision = "reject"
                reason = "Bình luận chứa từ ngữ không phù hợp"
            elif predicted_label == 0 and confidence > 0.7:
                # Only approve clearly positive comments
                decision = "approve"
                reason = f"Bình luận tích cực (Label {predicted_label})"
            elif predicted_label in [1, 2]:
                # Reject negative and toxic
                decision = "reject"
                reason = f"Bình luận tiêu cực/độc hại (Label {predicted_label})"
            else:
                # Low confidence
                decision = "reject"
                reason = f"Độ tin cậy thấp ({confidence:.2f})"
            
            return {
                "label": predicted_label,
                "confidence": float(confidence),
                "description": self.label_descriptions.get(predicted_label, "Unknown"),
                "decision": decision,
                "reason": reason,
                "processed_text": processed_text[:100] + "..." if len(processed_text) > 100 else processed_text,
                "probabilities": {
                    "label_0": float(probabilities[0][0]),
                    "label_1": float(probabilities[0][1]),
                    "label_2": float(probabilities[0][2])
                }
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi predict: {e}")
            return {
                "label": 1,  # Default safe label
                "confidence": 0.0,
                "description": "Lỗi trong quá trình phân loại",
                "error": str(e)
            }
    
    def predict_batch(self, texts: List[str], batch_size: int = 8) -> List[Dict]:
        """
        Phân loại nhiều bình luận cùng lúc
        
        Args:
            texts (List[str]): Danh sách bình luận
            batch_size (int): Kích thước batch để xử lý
            
        Returns:
            List[Dict]: Danh sách kết quả phân loại
        """
        if not self.is_loaded:
            return [{"label": 1, "confidence": 0.0, "error": "Model not loaded"} for _ in texts]
        
        results = []
        
        # Xử lý theo batch để tránh out of memory
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch_texts:
                result = self.predict_single(text)
                batch_results.append(result)
            
            results.extend(batch_results)
        
        return results
    
    def get_model_info(self) -> Dict:
        """
        Lấy thông tin về model đã load
        
        Returns:
            Dict: Thông tin model
        """
        return {
            "model_path": str(self.model_path),
            "is_loaded": self.is_loaded,
            "device": str(self.device),
            "labels": self.id2label,
            "label_descriptions": self.label_descriptions,
            "model_available": self.model is not None,
            "tokenizer_available": self.tokenizer is not None
        }

# Singleton instance để sử dụng trong toàn bộ ứng dụng
phobert_service = PhoBERTService()

def classify_comment(text: str) -> Dict:
    """
    Hàm helper để phân loại một bình luận
    
    Args:
        text (str): Nội dung bình luận
        
    Returns:
        Dict: Kết quả phân loại
    """
    return phobert_service.predict_single(text)

def classify_comments_batch(texts: List[str]) -> List[Dict]:
    """
    Hàm helper để phân loại nhiều bình luận
    
    Args:
        texts (List[str]): Danh sách bình luận
        
    Returns:
        List[Dict]: Danh sách kết quả phân loại
    """
    return phobert_service.predict_batch(texts) 