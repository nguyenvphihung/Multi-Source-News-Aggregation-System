-- Manual Database Fix cho bảng comments
-- Chạy trong PostgreSQL hoặc SQLite tùy loại database bạn dùng

-- Thêm cột likes (PostgreSQL)
ALTER TABLE comments ADD COLUMN IF NOT EXISTS likes INTEGER DEFAULT 0;

-- Thêm cột sentiment cho PhoBERT
ALTER TABLE comments ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20) DEFAULT 'neutral';

-- Thêm cột sentiment_confidence cho PhoBERT
ALTER TABLE comments ADD COLUMN IF NOT EXISTS sentiment_confidence FLOAT DEFAULT 0.0;

-- Kiểm tra schema sau khi thêm
-- PostgreSQL:
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'comments';

-- SQLite:
-- PRAGMA table_info(comments); 