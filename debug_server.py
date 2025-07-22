#!/usr/bin/env python3
"""
Script debug server và kiểm tra các component
"""
import sys
import traceback
import requests
import json

def check_dependencies():
    """Kiểm tra dependencies cần thiết"""
    print("📦 KIỂM TRA DEPENDENCIES:")
    print("="*40)
    
    required_packages = [
        ('torch', 'PyTorch for PhoBERT'),
        ('transformers', 'Hugging Face Transformers'),
        ('fastapi', 'Web framework'),
        ('sqlalchemy', 'Database ORM')
    ]
    
    missing = []
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - MISSING ({description})")
            missing.append(package)
    
    if missing:
        print(f"\n💡 Cài đặt: pip install {' '.join(missing)}")
        return False
    return True

def check_model_files():
    """Kiểm tra files PhoBERT model"""
    print("\n📁 KIỂM TRA MODEL FILES:")
    print("="*40)
    
    from pathlib import Path
    model_dir = Path("phobert_toxic_comment_model")
    
    required_files = [
        "config.json",
        "model.safetensors", 
        "tokenizer_config.json",
        "vocab.txt",
        "bpe.codes"
    ]
    
    if not model_dir.exists():
        print(f"❌ Thư mục {model_dir} không tồn tại!")
        return False
    
    missing_files = []
    for file in required_files:
        file_path = model_dir / file
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"✅ {file} ({size:,} bytes)")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_phobert_import():
    """Test import PhoBERT service"""
    print("\n🤖 KIỂM TRA PHOBERT SERVICE:")
    print("="*40)
    
    try:
        # Import PhoBERT service
        sys.path.append('app')
        from app.phobert_service import phobert_service
        
        print("✅ Import PhoBERT service thành công")
        print(f"📋 Model loaded: {phobert_service.is_loaded}")
        print(f"🖥️ Device: {phobert_service.device}")
        
        if phobert_service.is_loaded:
            print("✅ PhoBERT model đã sẵn sàng")
            
            # Test prediction
            test_text = "Bài viết hay quá!"
            result = phobert_service.predict_single(test_text)
            print(f"🔍 Test prediction: {result}")
            return True
        else:
            print("❌ PhoBERT model chưa load được")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi import PhoBERT: {e}")
        traceback.print_exc()
        return False

def test_comment_moderation():
    """Test comment moderation service"""
    print("\n🛡️ KIỂM TRA COMMENT MODERATION:")
    print("="*40)
    
    try:
        from app.comment_moderation import comment_moderation_service
        
        print("✅ Import comment moderation thành công")
        
        # Lấy thông tin moderation
        info = comment_moderation_service.get_moderation_info()
        print("📋 Moderation info:")
        for key, value in info.items():
            print(f"   {key}: {value}")
            
        return info.get('use_local_model', False)
        
    except Exception as e:
        print(f"❌ Lỗi comment moderation: {e}")
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test các API endpoints"""
    print("\n🌐 KIỂM TRA API ENDPOINTS:")
    print("="*40)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test moderation status
    try:
        response = requests.get(f"{base_url}/api/moderation-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ GET /api/moderation-status - OK")
            print(f"📋 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ GET /api/moderation-status - Error {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Không thể kết nối API: {e}")
        print("💡 Server có đang chạy không? python -m uvicorn main:app --reload")
        return False

def test_comment_submission():
    """Test submit comment"""
    print("\n📝 KIỂM TRA SUBMIT COMMENT:")
    print("="*40)
    
    base_url = "http://127.0.0.1:8000"
    
    test_data = {
        'article_id': 'BB-1846',
        'content': 'Test comment từ debug script',
        'notify_replies': False
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/comments",
            data=test_data,
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Submit comment thành công")
            return True
        else:
            print("❌ Submit comment thất bại")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi submit comment: {e}")
        return False

def main():
    """Chạy tất cả checks"""
    print("🔍 DEBUG SERVER VÀ PHOBERT INTEGRATION")
    print("="*60)
    
    checks = [
        ("Dependencies", check_dependencies),
        ("Model Files", check_model_files), 
        ("PhoBERT Import", test_phobert_import),
        ("Comment Moderation", test_comment_moderation),
        ("API Endpoints", test_api_endpoints),
        ("Comment Submission", test_comment_submission)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ FATAL ERROR in {name}: {e}")
            traceback.print_exc()
            results[name] = False
    
    # Tổng kết
    print(f"\n{'='*20} TỔNG KẾT {'='*20}")
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nKết quả: {passed}/{total} checks passed")
    
    if passed < total:
        print("\n💡 KHUYẾN NGHỊ:")
        if not results.get("Dependencies"):
            print("- Cài đặt dependencies: pip install -r requirements.txt")
        if not results.get("Model Files"):
            print("- Kiểm tra thư mục phobert_toxic_comment_model")
        if not results.get("PhoBERT Import"):
            print("- Model có thể quá lớn cho RAM, thử giảm batch size")
        if not results.get("API Endpoints"):
            print("- Khởi động lại server: python -m uvicorn main:app --reload")

if __name__ == "__main__":
    main() 