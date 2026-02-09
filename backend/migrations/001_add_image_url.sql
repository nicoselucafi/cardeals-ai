-- Add image_url column to offers table
-- Run this on Supabase SQL Editor

ALTER TABLE offers
ADD COLUMN IF NOT EXISTS image_url VARCHAR(500);

-- Add a comment explaining the column
COMMENT ON COLUMN offers.image_url IS 'URL to vehicle image from dealer/manufacturer source';
