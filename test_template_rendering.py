#!/usr/bin/env python3
"""
🔍 TEST TEMPLATE RENDERING
=========================
Debug template rendering để xem tại sao comments không hiển thị trên web
"""

import requests
import re

def test_web_page():
    """Test web page có load comments không"""
    print("🌐 TEST WEB PAGE RENDERING")
    print("="*50)
    
    try:
        # Test page load
        response = requests.get("http://127.0.0.1:8000/news/BB-1934", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Page load failed: {response.status_code}")
            return
        
        html_content = response.text
        print(f"✅ Page loaded: {response.status_code}")
        print(f"📊 HTML length: {len(html_content):,} characters")
        
        # Check for comments in HTML
        comment_patterns = [
            r'class="comment-item"',
            r'class="comment-content"',
            r'comment-avatar',
            r'Bài viết hay quá',
            r'đm',
            r'Tệ quá'
        ]
        
        comments_found = 0
        for pattern in comment_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                print(f"✅ Found '{pattern}': {len(matches)} times")
                comments_found += len(matches)
            else:
                print(f"❌ Not found: '{pattern}'")
        
        print(f"📊 Total comment-related elements: {comments_found}")
        
        # Check for specific comment content
        if "Bài viết hay quá" in html_content:
            print("✅ Found 'Bài viết hay quá' comment in HTML")
        else:
            print("❌ 'Bài viết hay quá' comment NOT in HTML")
        
        # Check for error messages
        if "error" in html_content.lower():
            print("⚠️ Found 'error' in HTML")
        
        # Check template structure
        if 'id="commentForm"' in html_content:
            print("✅ Comment form found")
        else:
            print("❌ Comment form NOT found")
        
        # Check for comments section
        if "comments" in html_content.lower():
            print("✅ Comments section found")
        else:
            print("❌ Comments section NOT found")
        
        # Save HTML for manual inspection
        with open("debug_page_output.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("📄 HTML saved to debug_page_output.html")
        
    except Exception as e:
        print(f"❌ Web test failed: {e}")

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🔌 TEST API ENDPOINTS")
    print("="*50)
    
    try:
        # Test comment submission
        form_data = {
            'article_id': 'BB-1934',
            'content': 'Test comment from script'
        }
        
        response = requests.post(
            "http://127.0.0.1:8000/api/comments",
            data=form_data,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Comment API working:")
            print(f"   success: {data.get('success')}")
            print(f"   status: {data.get('status')}")
            print(f"   message: {data.get('message')}")
        else:
            print(f"❌ Comment API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")

def main():
    print("🔍 DEBUG TEMPLATE RENDERING & WEB DISPLAY")
    print("="*50)
    
    test_web_page()
    test_api_endpoints()
    
    print("\n💡 DEBUGGING CHECKLIST:")
    print("="*50)
    print("1. ✅ Database có comments")
    print("2. ✅ Template query hoạt động")
    print("3. ? Web page rendering - check above")
    print("4. ? Browser cache - try hard refresh")
    print("5. ? Template logic - check debug_page_output.html")

if __name__ == "__main__":
    main() 