-- Manual SQL Fix cho PostgreSQL
-- Copy và paste vào psql hoặc database GUI

-- Thêm cột status (cần thiết ngay)
ALTER TABLE comments ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';

-- Thêm các cột khác cho PhoBERT (optional)
ALTER TABLE comments ADD COLUMN IF NOT EXISTS sentiment VARCHAR(20) DEFAULT 'neutral';
ALTER TABLE comments ADD COLUMN IF NOT EXISTS sentiment_confidence FLOAT DEFAULT 0.0;

-- Verify schema sau khi thêm
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'comments' 
ORDER BY ordinal_position; 