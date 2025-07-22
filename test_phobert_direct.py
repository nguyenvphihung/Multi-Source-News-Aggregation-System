#!/usr/bin/env python3
"""
Test PhoBERT model trực tiếp với comment "dm"
"""
import sys
import os
sys.path.append('app')

def test_phobert_model():
    """Test PhoBERT model trực tiếp"""
    print("🤖 TEST PHOBERT MODEL TRỰC TIẾP")
    print("="*40)
    
    try:
        # Import PhoBERT service
        from app.phobert_service import phobert_service, classify_comment
        
        print(f"📊 Model info:")
        print(f"  - Is loaded: {phobert_service.is_loaded}")
        print(f"  - Device: {phobert_service.device}")
        
        if not phobert_service.is_loaded:
            print("❌ PhoBERT model CHƯA LOAD!")
            print("💡 Đây là lý do tại sao 'dm' không bị reject")
            return False
        
        # Test với comment "dm"
        test_comments = [
            "dm",
            "Dm", 
            "dm thằng nào viết bài này",
            "Bài viết hay quá!",
            "Cảm ơn tác giả"
        ]
        
        print(f"\n🧪 TEST CLASSIFICATION:")
        print("-" * 50)
        
        for comment in test_comments:
            result = classify_comment(comment)
            
            label = result.get("label", "unknown")
            confidence = result.get("confidence", 0.0)
            description = result.get("description", "unknown")
            
            # Predict decision
            if label in [0, 1] and confidence > 0.6:
                decision = "✅ APPROVE"
            else:
                decision = "❌ REJECT"
            
            print(f"Input: '{comment}'")
            print(f"  → Label: {label} ({description})")
            print(f"  → Confidence: {confidence:.2f}")
            print(f"  → Decision: {decision}")
            print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Kiểm tra dependencies: pip install torch transformers")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comment_moderation():
    """Test comment moderation service"""
    print("\n🛡️ TEST COMMENT MODERATION SERVICE")
    print("="*40)
    
    try:
        from app.comment_moderation import comment_moderation_service
        
        # Get moderation info
        info = comment_moderation_service.get_moderation_info()
        
        print("📋 Moderation Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Test add comment for moderation
        if info.get('use_local_model') and info.get('phobert_model_loaded'):
            print("\n🧪 Test processing comment 'dm':")
            comment_id = comment_moderation_service.add_comment_for_moderation(
                content="dm",
                article_id="BB-1934", 
                user_id=1
            )
            print(f"✅ Processed with ID: {comment_id}")
        else:
            print("\n⚠️ PhoBERT not ready, using Colab workflow")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all tests"""
    print("🔍 DEBUG: TẠI SAO 'dm' KHÔNG BỊ REJECT?")
    print("="*50)
    
    # Test 1: PhoBERT model
    phobert_ok = test_phobert_model()
    
    # Test 2: Comment moderation
    test_comment_moderation()
    
    # Summary
    print("\n📊 SUMMARY:")
    print("="*30)
    if not phobert_ok:
        print("❌ PhoBERT model chưa load → Comments sẽ qua Colab workflow")
        print("💡 Fix: Chạy debug_server.py để kiểm tra PhoBERT")
        print("💡 Hoặc: Cài đặt dependencies thiếu")
    else:
        print("✅ PhoBERT model hoạt động → Check classification results above")

if __name__ == "__main__":
    main() 