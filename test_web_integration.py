#!/usr/bin/env python3
"""
Script test tích hợp PhoBERT trên web interface
"""
import requests
import time
import json

def test_moderation_status():
    """Test API moderation status"""
    print("🔍 KIỂM TRA MODERATION STATUS")
    print("="*40)
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/moderation-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API moderation-status hoạt động")
            print(f"📋 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data.get('data', {})
        else:
            print(f"❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def test_comment_submission():
    """Test submit comments với các loại nội dung khác nhau"""
    print("\n📝 KIỂM TRA SUBMIT COMMENTS")
    print("="*40)
    
    test_cases = [
        {
            "content": "Bài viết rất hay và bổ ích, cảm ơn tác giả!",
            "expected": "approved",
            "description": "Comment tích cực"
        },
        {
            "content": "Mình không đồng ý với quan điểm này",
            "expected": "approved_or_pending",
            "description": "Comment tiêu cực nhẹ"
        },
        {
            "content": "dm thằng nào viết bài này, ngu vl",
            "expected": "rejected",
            "description": "Comment độc hại"
        },
        {
            "content": "Spam spam spam click here to win money!!!",
            "expected": "rejected", 
            "description": "Comment spam"
        }
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Content: '{test_case['content']}'")
        
        data = {
            'article_id': 'BB-1846',
            'content': test_case['content'],
            'notify_replies': False
        }
        
        try:
            response = requests.post(
                "http://127.0.0.1:8000/api/comments",
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                success = result.get('success', False)
                message = result.get('message', 'No message')
                
                print(f"   ✅ Response: {status}")
                print(f"   📋 Message: {message}")
                
                # Kiểm tra kết quả có đúng như expected không
                if test_case['expected'] == 'approved' and status == 'approved':
                    print("   🎯 PASS: Được phê duyệt như mong đợi")
                elif test_case['expected'] == 'rejected' and not success:
                    print("   🎯 PASS: Bị từ chối như mong đợi")
                elif test_case['expected'] == 'approved_or_pending' and status in ['approved', 'pending_moderation']:
                    print("   🎯 PASS: Kết quả hợp lý")
                else:
                    print(f"   ⚠️ UNEXPECTED: Expected {test_case['expected']}, got {status}")
                
                results.append({
                    'test_case': test_case,
                    'result': result,
                    'success': True
                })
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                print(f"   Response: {response.text}")
                results.append({
                    'test_case': test_case,
                    'result': None,
                    'success': False
                })
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'test_case': test_case,
                'result': None,
                'success': False
            })
        
        time.sleep(1)  # Pause between requests
    
    return results

def test_web_features():
    """Test các tính năng web"""
    print("\n🌐 KIỂM TRA WEB FEATURES")
    print("="*40)
    
    # Test trang news detail
    try:
        response = requests.get("http://127.0.0.1:8000/news/BB-1846", timeout=5)
        if response.status_code == 200:
            print("✅ Trang news detail load thành công")
            
            # Check các thành phần quan trọng
            html_content = response.text
            features = {
                'moderation-status element': 'id="moderation-status"' in html_content,
                'comment-preview-warning': 'id="comment-preview-warning"' in html_content,
                'phobert-notification CSS': '.phobert-notification' in html_content,
                'real-time check': 'checkCommentContent' in html_content,
                'PhoBERT integration': 'showSuccessMessage' in html_content
            }
            
            for feature, exists in features.items():
                status = "✅" if exists else "❌"
                print(f"   {status} {feature}")
                
        else:
            print(f"❌ Trang news detail lỗi: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Lỗi test web: {e}")

def print_summary(moderation_info, comment_results):
    """In tổng kết"""
    print("\n" + "="*60)
    print("📊 TỔNG KẾT INTEGRATION TEST")
    print("="*60)
    
    # Moderation system status
    if moderation_info:
        use_local = moderation_info.get('use_local_model', False)
        model_loaded = moderation_info.get('phobert_model_loaded', False)
        
        print(f"🤖 PhoBERT Model: {'✅ Loaded' if model_loaded else '❌ Not loaded'}")
        print(f"🔄 Workflow: {'Local PhoBERT' if use_local else 'Colab'}")
        
        if use_local and model_loaded:
            device = moderation_info.get('phobert_device', 'Unknown')
            print(f"🖥️ Device: {device}")
    
    # Comment test results
    if comment_results:
        total_tests = len(comment_results)
        successful_tests = sum(1 for r in comment_results if r['success'])
        
        print(f"\n📝 Comment Tests: {successful_tests}/{total_tests} passed")
        
        # Breakdown by expected result
        approved = sum(1 for r in comment_results if r['success'] and r['result'] and r['result'].get('status') == 'approved')
        rejected = sum(1 for r in comment_results if r['success'] and not r['result'].get('success', True))
        pending = sum(1 for r in comment_results if r['success'] and r['result'] and r['result'].get('status') == 'pending_moderation')
        
        print(f"   ✅ Approved: {approved}")
        print(f"   ❌ Rejected: {rejected}")
        print(f"   ⏳ Pending: {pending}")
    
    print(f"\n💡 Next Steps:")
    if not moderation_info or not moderation_info.get('phobert_model_loaded'):
        print("   - Chạy debug_server.py để kiểm tra PhoBERT model")
        print("   - Cài đặt dependencies: pip install torch transformers")
    else:
        print("   - Hệ thống đã sẵn sàng!")
        print("   - Test trên browser: http://127.0.0.1:8000/news/BB-1846")
        print("   - Nhập comment để xem PhoBERT hoạt động")

def main():
    """Chạy tất cả tests"""
    print("🧪 KIỂM TRA TÍCH HỢP PHOBERT WEB INTERFACE")
    print("="*60)
    
    # Test 1: Moderation status
    moderation_info = test_moderation_status()
    
    # Test 2: Comment submission
    comment_results = test_comment_submission()
    
    # Test 3: Web features
    test_web_features()
    
    # Summary
    print_summary(moderation_info, comment_results)

if __name__ == "__main__":
    main() 