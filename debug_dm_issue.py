#!/usr/bin/env python3
"""
🚨 DEBUG: TẠI SAO "đm" ĐƯỢC APPROVE?
==================================
Script debug chuyên biệt để tìm nguyên nhân "đm" không bị reject
"""

def check_dependencies():
    """Kiểm tra dependencies"""
    print("🔍 KIỂM TRA DEPENDENCIES")
    print("="*40)
    
    try:
        import torch
        print(f"✅ torch version: {torch.__version__}")
    except ImportError:
        print("❌ torch MISSING")
        return False
    
    try:
        import transformers
        print(f"✅ transformers version: {transformers.__version__}")
    except ImportError:
        print("❌ transformers MISSING")
        return False
    
    try:
        import tokenizers
        print(f"✅ tokenizers version: {tokenizers.__version__}")
    except ImportError:
        print("❌ tokenizers MISSING")
        return False
    
    return True

def test_phobert_import():
    """Test import PhoBERT service"""
    print("\n🤖 TEST PHOBERT IMPORT")
    print("="*40)
    
    try:
        from app.phobert_service import phobert_service, classify_comment
        print(f"✅ PhoBERT import successful")
        print(f"📊 Model loaded: {phobert_service.is_loaded}")
        print(f"📊 Device: {phobert_service.device}")
        
        if phobert_service.is_loaded:
            return True, classify_comment
        else:
            print(f"❌ PhoBERT model KHÔNG LOAD được")
            return False, None
            
    except Exception as e:
        print(f"❌ PhoBERT import FAILED: {e}")
        return False, None

def test_dm_classification(classify_function):
    """Test classification với "đm" cụ thể"""
    print("\n🧪 TEST 'đm' CLASSIFICATION")
    print("="*40)
    
    test_cases = ["đm", "dm", "ĐM", "DM"]
    
    for text in test_cases:
        print(f"\n📝 Testing: '{text}'")
        try:
            result = classify_function(text)
            
            label = result.get("label")
            confidence = result.get("confidence", 0.0)
            decision = result.get("decision")
            reason = result.get("reason")
            
            print(f"   Label: {label}")
            print(f"   Confidence: {confidence:.3f}")
            print(f"   Decision: {decision}")
            print(f"   Reason: {reason}")
            
            # Check if it should be rejected
            if decision == "reject":
                print(f"   ✅ CORRECT: Toxic comment rejected")
            else:
                print(f"   ❌ BUG: Toxic comment được approve!")
                print(f"       → Đây chính là nguyên nhân!")
                
        except Exception as e:
            print(f"   ❌ Error classifying '{text}': {e}")

def test_api_direct():
    """Test API trực tiếp với "đm" """
    print("\n🌐 TEST API DIRECT")
    print("="*40)
    
    try:
        import requests
        
        # Test comment submission
        form_data = {
            'article_id': 'BB-1934',
            'content': 'đm'
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/api/comments",
            data=form_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            success = data.get('success')
            status = data.get('status')
            message = data.get('message')
            
            print(f"📝 API Response cho 'đm':")
            print(f"   success: {success}")
            print(f"   status: {status}")
            print(f"   message: {message}")
            
            if success and status == "approved":
                print(f"   ❌ BUG CONFIRMED: 'đm' được approve qua API!")
            elif not success and status == "rejected":
                print(f"   ✅ CORRECT: 'đm' bị reject qua API")
            else:
                print(f"   ⚠️ UNKNOWN: Unexpected status")
                
        else:
            print(f"❌ API error {response.status_code}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("💡 Đảm bảo server đang chạy: python -m uvicorn main:app --reload")

def check_fallback_logic():
    """Kiểm tra xem có fallback to normal save không"""
    print("\n🔄 CHECK FALLBACK LOGIC")
    print("="*40)
    
    # Check if the code is falling back to normal save instead of using PhoBERT
    try:
        from app.phobert_service import phobert_service
        
        if not phobert_service.is_loaded:
            print("❌ PhoBERT NOT LOADED → Fallback to normal save")
            print("💡 Đây có thể là nguyên nhân 'đm' được approve")
            return False
        else:
            print("✅ PhoBERT IS LOADED → Should use AI classification")
            return True
            
    except ImportError:
        print("❌ PhoBERT service IMPORT ERROR → Fallback to normal save")
        print("💡 Đây chính là nguyên nhân 'đm' được approve")
        return False

def main():
    print("🚨 DEBUG: TẠI SAO 'đm' ĐƯỢC APPROVE?")
    print("="*50)
    
    # Step 1: Check dependencies
    deps_ok = check_dependencies()
    
    # Step 2: Test PhoBERT import
    phobert_ok, classify_func = test_phobert_import()
    
    # Step 3: Test classification if PhoBERT works
    if phobert_ok and classify_func:
        test_dm_classification(classify_func)
    
    # Step 4: Check fallback logic
    fallback_check = check_fallback_logic()
    
    # Step 5: Test API
    test_api_direct()
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("="*50)
    
    print(f"Dependencies: {'✅' if deps_ok else '❌'}")
    print(f"PhoBERT Loading: {'✅' if phobert_ok else '❌'}")
    print(f"No Fallback: {'✅' if fallback_check else '❌'}")
    
    if not deps_ok:
        print("\n🚨 ROOT CAUSE: Missing dependencies")
        print("💡 FIX: pip install torch transformers tokenizers")
        
    elif not phobert_ok:
        print("\n🚨 ROOT CAUSE: PhoBERT không load được")
        print("💡 FIX: Kiểm tra model files hoặc dependencies")
        
    elif not fallback_check:
        print("\n🚨 ROOT CAUSE: PhoBERT không sẵn sàng → fallback to normal save")
        print("💡 FIX: Debug PhoBERT loading")
        
    else:
        print("\n🚨 ROOT CAUSE: PhoBERT classify sai hoặc logic bug")
        print("💡 FIX: Kiểm tra model performance hoặc decision logic")

if __name__ == "__main__":
    main() 