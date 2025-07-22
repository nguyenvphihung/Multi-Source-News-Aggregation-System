#!/usr/bin/env python3
"""
🚀 QUICK START: PHOBERT TOXIC COMMENT CLASSIFIER
==============================================
Chạy script này để setup và test PhoBERT workflow ngay lập tức!

Usage: python quick_start.py
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run command và hiển thị kết quả"""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        return False

def main():
    print("🎯 PHOBERT QUICK START")
    print("=" * 50)
    print("Ý tưởng: Phân loại trực tiếp bình luận với PhoBERT")
    print("- Label 0/1 → Lưu DB + hiển thị ngay")
    print("- Label 2 → Reject + thông báo đỏ")
    
    # Step 1: Install dependencies
    print(f"\n📦 STEP 1: Cài đặt dependencies...")
    deps_success = run_command(
        "pip install torch transformers tokenizers", 
        "Installing PhoBERT dependencies"
    )
    
    if not deps_success:
        print("❌ Không thể cài dependencies. Thử manual:")
        print("pip install torch transformers tokenizers")
        return
    
    # Step 2: Test PhoBERT loading
    print(f"\n🤖 STEP 2: Test PhoBERT loading...")
    test_success = run_command(
        "python test_phobert_direct.py",
        "Testing PhoBERT model loading"
    )
    
    # Step 3: Fix database if needed
    print(f"\n🗄️ STEP 3: Fix database schema...")
    db_success = run_command(
        "python fix_database_schema.py",
        "Fixing database schema"
    )
    
    # Step 4: Complete workflow test
    print(f"\n🧪 STEP 4: Complete workflow test...")
    workflow_success = run_command(
        "python test_complete_workflow.py",
        "Testing complete workflow"
    )
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    
    steps = [
        ("Dependencies", deps_success),
        ("PhoBERT Loading", test_success),
        ("Database Schema", db_success),
        ("Complete Workflow", workflow_success)
    ]
    
    passed = sum(1 for _, success in steps if success)
    total = len(steps)
    
    for step_name, success in steps:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    print(f"\n📈 Result: {passed}/{total} steps completed")
    
    if passed >= 3:  # At least dependencies + PhoBERT working
        print(f"\n🎉 SETUP THÀNH CÔNG!")
        print(f"🚀 Khởi động server:")
        print(f"   python -m uvicorn main:app --reload")
        print(f"\n🌐 Test trên web:")
        print(f"   http://127.0.0.1:8000/news/BB-1934")
        print(f"\n💡 Test cases:")
        print(f"   - Nhập 'dm' → Expect: 🚫 Notification đỏ")
        print(f"   - Nhập 'Bài hay!' → Expect: 🎉 Notification xanh + reload")
        
    else:
        print(f"\n🚨 CẦN FIX ISSUES")
        print(f"💡 Chạy manual commands trong PHOBERT_SETUP_GUIDE.md")

if __name__ == "__main__":
    main() 