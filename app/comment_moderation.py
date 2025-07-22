"""
Module xử lý moderation bình luận với PhoBERT model local
Workflow: Comment -> PhoBERT Prediction -> Decision -> Database/Delete
"""
import os
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class CommentModerationService:
    """Service để xử lý moderation bình luận với PhoBERT model local và Colab backup"""
    
    def __init__(self, pending_dir="pending_comments", use_local_model=True):
        """
        Khởi tạo service
        
        Args:
            pending_dir (str): Thư mục chứa comments chờ xử lý
            use_local_model (bool): Sử dụng PhoBERT local hoặc Colab workflow
        """
        self.pending_dir = Path(pending_dir)
        self.pending_dir.mkdir(exist_ok=True)
        self.use_local_model = use_local_model
        
        # File chứa comments chờ gửi lên Colab (cho backup workflow)
        self.pending_csv = self.pending_dir / "comments_for_colab.csv"
        
        # File chứa mapping giữa comment_id và thông tin bình luận
        self.comment_mapping = self.pending_dir / "comment_mapping.json"
        
        # Import PhoBERT service nếu sử dụng local model
        if self.use_local_model:
            try:
                from app.phobert_service import phobert_service
                self.phobert_service = phobert_service
                print("✅ PhoBERT service đã được tích hợp vào comment moderation")
            except ImportError as e:
                print(f"⚠️ Không thể import PhoBERT service: {e}")
                print("   Chuyển sang sử dụng Colab workflow...")
                self.use_local_model = False
    
    def add_comment_for_moderation(self, content: str, article_id: str, 
                                 user_id: int, parent_id: int = None) -> str:
        """
        Thêm bình luận vào moderation workflow (Local PhoBERT hoặc Colab)
        
        Args:
            content (str): Nội dung bình luận
            article_id (str): ID bài viết
            user_id (int): ID người dùng
            parent_id (int, optional): ID bình luận cha (nếu là reply)
            
        Returns:
            str: Unique comment ID để tracking
        """
        comment_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        comment_data = {
            "content": content,
            "article_id": article_id,
            "user_id": user_id,
            "parent_id": parent_id,
            "timestamp": timestamp,
            "status": "pending"
        }
        
        if self.use_local_model and hasattr(self, 'phobert_service'):
            # Workflow mới: Xử lý trực tiếp với PhoBERT local
            return self._process_comment_with_phobert(comment_id, comment_data)
        else:
            # Workflow cũ: Gửi lên Colab
            self._save_comment_mapping(comment_id, comment_data)
        self._add_to_csv(comment_id, content)
            return comment_id
    
    def _process_comment_with_phobert(self, comment_id: str, comment_data: Dict[str, Any]) -> str:
        """
        Xử lý comment trực tiếp với PhoBERT model local
        
        Args:
            comment_id (str): ID của comment
            comment_data (Dict): Thông tin comment
            
        Returns:
            str: Comment ID
        """
        try:
            content = comment_data["content"]
            
            # Phân loại với PhoBERT
            prediction = self.phobert_service.predict_single(content)
            label = prediction.get("label")
            confidence = prediction.get("confidence", 0.0)
            decision = prediction.get("decision")
            reason = prediction.get("reason")
            
            print(f"🤖 PhoBERT Prediction - Label: {label}, Confidence: {confidence:.2f}, Decision: {decision}")
            print(f"📝 Comment: {content[:50]}...")
            print(f"💡 Reason: {reason}")
            
            # Cập nhật comment_data với kết quả PhoBERT
            comment_data["phobert_label"] = label
            comment_data["phobert_confidence"] = confidence
            comment_data["phobert_decision"] = decision
            comment_data["phobert_reason"] = reason
            comment_data["processed_at"] = datetime.now().isoformat()
            
            # Quyết định dựa trên PhoBERT decision
            if decision == "approve":
                comment_data["status"] = "approved"
                
                # Lưu trực tiếp vào database
                try:
                    self._save_comment_to_database(comment_data, label)
                    print(f"✅ Comment {comment_id[:8]} đã được lưu vào database")
                    comment_data["saved_to_db"] = True
                except Exception as e:
                    print(f"❌ Lỗi lưu database: {e}")
                    comment_data["saved_to_db"] = False
                    comment_data["db_error"] = str(e)
                
            else:  # decision == "reject"
                comment_data["status"] = "rejected"
                comment_data["saved_to_db"] = False
                print(f"❌ Comment {comment_id[:8]} bị từ chối - {reason}")
            
            # Lưu thông tin vào mapping file để tracking
            self._save_comment_mapping(comment_id, comment_data)
            
            return comment_id
            
        except Exception as e:
            print(f"❌ Lỗi khi xử lý comment với PhoBERT: {e}")
            # Fallback: Lưu vào Colab workflow
            comment_data["status"] = "error"
            comment_data["error"] = str(e)
            self._save_comment_mapping(comment_id, comment_data)
            self._add_to_csv(comment_id, content)
        return comment_id
    
    def _save_comment_mapping(self, comment_id: str, comment_data: Dict[str, Any]):
        """Lưu mapping giữa comment_id và thông tin comment"""
        mapping = {}
        if self.comment_mapping.exists():
            with open(self.comment_mapping, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        
        mapping[comment_id] = comment_data
        
        with open(self.comment_mapping, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    def _add_to_csv(self, comment_id: str, content: str):
        """Thêm comment vào CSV file để gửi lên Colab"""
        file_exists = self.pending_csv.exists()
        
        with open(self.pending_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Ghi header nếu file mới
            if not file_exists:
                writer.writerow(['comment_id', 'content', 'timestamp'])
            
            writer.writerow([comment_id, content, datetime.now().isoformat()])
    
    def get_pending_comments_csv_path(self) -> str:
        """Lấy đường dẫn file CSV để upload lên Colab"""
        return str(self.pending_csv)
    
    def process_colab_results(self, results: list) -> Dict[str, Any]:
        """
        Xử lý kết quả từ Colab và quyết định lưu/xóa comment
        
        Args:
            results (list): Danh sách kết quả từ Colab 
                          [{"comment_id": "xxx", "label": 0}, ...]
                          
        Returns:
            Dict: Thống kê kết quả xử lý
        """
        stats = {
            "total_processed": 0,
            "saved_to_db": 0,
            "deleted": 0,
            "errors": 0,
            "saved_comments": [],
            "deleted_comments": []
        }
        
        # Load comment mapping
        if not self.comment_mapping.exists():
            return stats
            
        with open(self.comment_mapping, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        for result in results:
            stats["total_processed"] += 1
            comment_id = result.get("comment_id")
            label = result.get("label")
            
            if comment_id not in mapping:
                stats["errors"] += 1
                continue
            
            comment_data = mapping[comment_id]
            
            try:
                if label in [0, 1]:  # Label 0 hoặc 1 -> Lưu vào database
                    self._save_comment_to_database(comment_data, label)
                    stats["saved_to_db"] += 1
                    stats["saved_comments"].append({
                        "comment_id": comment_id,
                        "content": comment_data["content"][:50] + "...",
                        "label": label
                    })
                    
                elif label == 2:  # Label 2 -> Xóa
                    stats["deleted"] += 1
                    stats["deleted_comments"].append({
                        "comment_id": comment_id,
                        "content": comment_data["content"][:50] + "...",
                        "reason": "Label 2 - Content filtered"
                    })
                
                # Đánh dấu đã xử lý
                mapping[comment_id]["status"] = "processed"
                mapping[comment_id]["label"] = label
                mapping[comment_id]["processed_at"] = datetime.now().isoformat()
                
            except Exception as e:
                stats["errors"] += 1
                print(f"Error processing comment {comment_id}: {e}")
        
        # Cập nhật mapping file
        with open(self.comment_mapping, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        
        # Dọn dẹp CSV file đã xử lý
        self._cleanup_processed_csv()
        
        return stats
    
    def _save_comment_to_database(self, comment_data: Dict[str, Any], label: int):
        """Lưu comment vào database"""
        from app.database import SessionLocal
        from app.models import Comment, Article
        
        db = SessionLocal()
        try:
            # Kiểm tra bài viết và user vẫn tồn tại
            article = db.query(Article).filter(Article.article_id == comment_data["article_id"]).first()
            if not article:
                raise Exception(f"Article {comment_data['article_id']} not found")
            
            # Tạo comment mới
            new_comment = Comment(
                article_id=comment_data["article_id"],
                user_id=comment_data["user_id"],
                content=comment_data["content"],
                parent_id=comment_data.get("parent_id"),
                sentiment="positive" if label == 0 else "negative",  # Map label to sentiment
                sentiment_confidence=0.9  # High confidence vì đã qua Colab
            )
            
            db.add(new_comment)
            
            # Cập nhật count cho article
            article.comments_count = db.query(Comment).filter(Comment.article_id == comment_data["article_id"]).count() + 1
            
            db.commit()
            
            # Lưu vào CSV để training
            from app.utils import save_comment_to_csv
            save_comment_to_csv(
                comment_data["content"], 
                "moderated_comment", 
                comment_data["article_id"]
            )
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    def _cleanup_processed_csv(self):
        """Dọn dẹp file CSV sau khi xử lý"""
        if self.pending_csv.exists():
            # Backup file cũ
            backup_name = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            backup_path = self.pending_dir / backup_name
            self.pending_csv.rename(backup_path)
            
            # Tạo file CSV mới rỗng cho lần sau
            self.pending_csv.touch()
    
    def get_pending_count(self) -> int:
        """Lấy số lượng comment đang chờ xử lý"""
        if not self.comment_mapping.exists():
            return 0
            
        with open(self.comment_mapping, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
            
        return len([c for c in mapping.values() if c.get("status") == "pending"])
    
    def export_for_colab(self) -> Dict[str, Any]:
        """Export dữ liệu để gửi lên Colab"""
        pending_count = self.get_pending_count()
        
        return {
            "csv_file_path": str(self.pending_csv),
            "pending_count": pending_count,
            "file_exists": self.pending_csv.exists(),
            "instructions": {
                "step_1": "Upload file CSV lên Google Colab",
                "step_2": "Chạy model prediction trên từng dòng",
                "step_3": "Gửi kết quả về endpoint /api/process-colab-results",
                "csv_format": "comment_id,content,timestamp",
                "result_format": '[{"comment_id": "xxx", "label": 0}, {"comment_id": "yyy", "label": 1}]'
            }
        }
    
    def get_moderation_info(self) -> Dict[str, Any]:
        """Lấy thông tin về hệ thống moderation hiện tại"""
        info = {
            "use_local_model": self.use_local_model,
            "pending_count": self.get_pending_count(),
            "csv_file_exists": self.pending_csv.exists()
        }
        
        if self.use_local_model and hasattr(self, 'phobert_service'):
            phobert_info = self.phobert_service.get_model_info()
            info.update({
                "phobert_model_loaded": phobert_info["is_loaded"],
                "phobert_device": phobert_info["device"],
                "phobert_labels": phobert_info["label_descriptions"]
            })
        else:
            info.update({
                "phobert_model_loaded": False,
                "colab_workflow": "active"
            })
        
        return info
    
    def switch_to_local_model(self) -> bool:
        """Chuyển sang sử dụng PhoBERT local model"""
        try:
            from app.phobert_service import phobert_service
            self.phobert_service = phobert_service
            if self.phobert_service.is_loaded:
                self.use_local_model = True
                print("✅ Đã chuyển sang sử dụng PhoBERT local model")
                return True
            else:
                print("❌ PhoBERT model chưa được load thành công")
                return False
        except ImportError as e:
            print(f"❌ Không thể import PhoBERT service: {e}")
            return False
    
    def switch_to_colab_workflow(self) -> bool:
        """Chuyển sang sử dụng Colab workflow"""
        self.use_local_model = False
        print("✅ Đã chuyển sang sử dụng Colab workflow")
        return True

# Singleton instance
comment_moderation_service = CommentModerationService() 