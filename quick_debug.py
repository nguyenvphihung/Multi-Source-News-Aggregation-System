#!/usr/bin/env python3
"""
Script nhanh check trạng thái moderation system
"""
import requests
import json

def check_status():
    """Kiểm tra status nhanh"""
    print("🔍 KIỂM TRA NHANH TRẠNG THÁI HỆ THỐNG")
    print("="*50)
    
    try:
        # Check moderation status
        response = requests.get("http://127.0.0.1:8000/api/moderation-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            info = data.get('data', {})
            
            print("📊 MODERATION STATUS:")
            print(f"  Use Local Model: {info.get('use_local_model', 'Unknown')}")
            print(f"  PhoBERT Loaded: {info.get('phobert_model_loaded', 'Unknown')}")
            print(f"  Device: {info.get('phobert_device', 'Unknown')}")
            print(f"  Pending Count: {info.get('pending_count', 0)}")
            
            # Recommend action
            if info.get('use_local_model') and info.get('phobert_model_loaded'):
                print("\n✅ HỆ THỐNG HOẠT ĐỘNG BÌNH THƯỜNG")
                print("💡 Status indicator sẽ chuyển thành: '🤖 AI PhoBERT đang hoạt động'")
            else:
                print("\n⚠️ PHOBERT MODEL CHƯA SẴN SÀNG")
                print("💡 Đang dùng Colab workflow")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("💡 Server có đang chạy không?")

def test_comment():
    """Test submit comment nhanh"""
    print("\n🧪 TEST SUBMIT COMMENT:")
    print("="*30)
    
    test_data = {
        'article_id': 'BB-1934',
        'content': 'Test comment từ script',
        'notify_replies': False
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8000/api/comments",
            data=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result.get('success')}")
            print(f"📋 Status: {result.get('status')}")
            print(f"💬 Message: {result.get('message')}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_status()
    test_comment()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Refresh trang web để thấy status indicator update")
    print("2. Test submit comment 'dm' trên web")
    print("3. Test submit comment tích cực") 
    print("4. Nếu PhoBERT chưa load: chạy debug_server.py") 