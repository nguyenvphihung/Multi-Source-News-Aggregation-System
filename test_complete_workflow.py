#!/usr/bin/env python3
"""
🎯 TEST COMPLETE PHOBERT WORKFLOW
=================================
Script kiểm tra toàn bộ workflow PhoBERT từ dependencies → model loading → classification → web integration

Usage: python test_complete_workflow.py
"""

import sys
import os
import requests
import json
from pathlib import Path

def print_section(title):
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print('='*50)

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    print_section("KIỂM TRA DEPENDENCIES")
    
    dependencies = ['torch', 'transformers', 'tokenizers', 'fastapi', 'sqlalchemy']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} - OK")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing.append(dep)
    
    if missing:
        print(f"\n🚨 THIẾU DEPENDENCIES: {', '.join(missing)}")
        print(f"💡 Chạy: pip install {' '.join(missing)}")
        return False
    else:
        print(f"\n✅ TẤT CẢ DEPENDENCIES ĐÃ SẴN SÀNG")
        return True

def check_model_files():
    """Kiểm tra PhoBERT model files"""
    print_section("KIỂM TRA PHOBERT MODEL FILES")
    
    model_dir = Path("phobert_toxic_comment_model")
    required_files = [
        "config.json",
        "model.safetensors", 
        "tokenizer_config.json",
        "vocab.txt",
        "bpe.codes",
        "special_tokens_map.json",
        "added_tokens.json"
    ]
    
    if not model_dir.exists():
        print(f"❌ Model directory không tồn tại: {model_dir}")
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
    
    if missing_files:
        print(f"\n🚨 THIẾU FILES: {', '.join(missing_files)}")
        return False
    else:
        print(f"\n✅ TẤT CẢ MODEL FILES ĐÃ SẴN SÀNG")
        return True

def test_phobert_loading():
    """Test PhoBERT service loading"""
    print_section("TEST PHOBERT SERVICE LOADING")
    
    try:
        from app.phobert_service import phobert_service, classify_comment
        
        print(f"📊 Model loaded: {phobert_service.is_loaded}")
        print(f"📊 Device: {phobert_service.device}")
        
        if phobert_service.is_loaded:
            info = phobert_service.get_model_info()
            print(f"📊 Model info: {info}")
            return True
        else:
            print("❌ PhoBERT không load được")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi import PhoBERT: {e}")
        return False

def test_phobert_classification():
    """Test PhoBERT classification với các test cases"""
    print_section("TEST PHOBERT CLASSIFICATION")
    
    try:
        from app.phobert_service import classify_comment
        
        test_cases = [
            ("dm", "Label 2 - Độc hại"),
            ("đm", "Label 2 - Độc hại"), 
            ("con chó", "Label 2 - Độc hại"),
            ("thằng lol", "Label 2 - Độc hại"),
            ("Bài viết hay quá!", "Label 0/1 - An toàn"),
            ("Cảm ơn tác giả", "Label 0/1 - An toàn"),
            ("Thông tin hữu ích", "Label 0/1 - An toàn"),
        ]
        
        all_passed = True
        
        for text, expected in test_cases:
            result = classify_comment(text)
            label = result.get("label")
            confidence = result.get("confidence", 0.0)
            decision = result.get("decision")
            reason = result.get("reason")
            
            print(f"\n📝 Input: '{text}'")
            print(f"   Label: {label} | Confidence: {confidence:.2f}")
            print(f"   Decision: {decision} | Reason: {reason}")
            print(f"   Expected: {expected}")
            
            # Validate toxic comments should be rejected
            if text in ["dm", "đm", "con chó", "thằng lol"]:
                if decision != "reject":
                    print(f"   ❌ FAILED: Toxic comment should be REJECTED but got {decision}")
                    all_passed = False
                else:
                    print(f"   ✅ PASSED: Toxic comment correctly REJECTED")
            
            # Validate safe comments should be approved
            elif "hay quá" in text or "Cảm ơn" in text or "hữu ích" in text:
                if decision != "approve":
                    print(f"   ❌ FAILED: Safe comment should be APPROVED but got {decision}")
                    all_passed = False
                else:
                    print(f"   ✅ PASSED: Safe comment correctly APPROVED")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Lỗi test classification: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print_section("TEST API ENDPOINTS")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test moderation status
    try:
        response = requests.get(f"{base_url}/api/moderation-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Moderation status API: {data}")
        else:
            print(f"❌ Moderation status API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Không thể kết nối API: {e}")
        print("💡 Đảm bảo server đang chạy: python -m uvicorn main:app --reload")
        return False
    
    return True

def test_comment_submission():
    """Test comment submission qua API"""
    print_section("TEST COMMENT SUBMISSION")
    
    base_url = "http://127.0.0.1:8000"
    
    test_comments = [
        ("Bài viết hay quá!", "should_approve"),
        ("dm", "should_reject"),
        ("Cảm ơn tác giả", "should_approve")
    ]
    
    for content, expected in test_comments:
        try:
            form_data = {
                'article_id': 'BB-1934',  # Test article
                'content': content
            }
            
            response = requests.post(
                f"{base_url}/api/comments",
                data=form_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('success')
                status = data.get('status')
                message = data.get('message')
                
                print(f"\n📝 Comment: '{content}'")
                print(f"   Response: success={success}, status={status}")
                print(f"   Message: {message}")
                
                if expected == "should_approve" and success and status == "approved":
                    print(f"   ✅ PASSED: Correctly approved")
                elif expected == "should_reject" and not success and status == "rejected":
                    print(f"   ✅ PASSED: Correctly rejected")
                else:
                    print(f"   ❌ FAILED: Expected {expected}, got success={success}, status={status}")
                    
            else:
                print(f"❌ API error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing comment '{content}': {e}")
            return False
    
    return True

def main():
    """Main test function"""
    print("🎯 PHOBERT COMPLETE WORKFLOW TEST")
    print("=" * 50)
    
    # Test checklist
    tests = [
        ("Dependencies", check_dependencies),
        ("Model Files", check_model_files), 
        ("PhoBERT Loading", test_phobert_loading),
        ("PhoBERT Classification", test_phobert_classification),
        ("API Endpoints", test_api_endpoints),
        ("Comment Submission", test_comment_submission)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n📊 TỔNG KẾT: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TẤT CẢ TESTS ĐỀU PASSED!")
        print("🚀 PhoBERT workflow đã sẵn sàng hoạt động!")
        print("\n💡 Thử nghiệm trên web:")
        print("   1. Mở http://127.0.0.1:8000/news/BB-1934")
        print("   2. Nhập 'dm' → Sẽ bị reject với notification đỏ")
        print("   3. Nhập 'Bài viết hay!' → Sẽ được approve với notification xanh + reload")
    else:
        print(f"\n🚨 CÒN {total - passed} TESTS FAILED!")
        print("💡 Cần fix các issues trước khi test trên web")

if __name__ == "__main__":
    main() 