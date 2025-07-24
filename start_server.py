#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple server starter script to avoid Unicode issues in terminal
"""
import uvicorn
import sys
import os

# Set UTF-8 encoding
if sys.platform.startswith('win'):
    import locale
    locale.setlocale(locale.LC_ALL, '')

def main():
    """Start the FastAPI server"""
    try:
        print("Starting FastAPI server...")
        uvicorn.run(
            "main:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
