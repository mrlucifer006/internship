-- SQL Command to drop the unique constraint on 'name' in the 'visitors' table.
-- This allows multiple visitors with the same name.

-- Drop the unique constraint (assuming standard naming convention or unique index)
-- Supabase/Postgres usually names unique constraints as <table_name>_<column_name>_key

ALTER TABLE visitors DROP CONSTRAINT IF EXISTS visitors_name_key;

-- If it was created as a unique index:
DROP INDEX IF EXISTS visitors_name_idx;
DROP INDEX IF EXISTS visitors_name_key;

-- [NEW] Add columns for Vehicle Data
ALTER TABLE vehicle ADD COLUMN IF NOT EXISTS tare_weight FLOAT;
ALTER TABLE vehicle ADD COLUMN IF NOT EXISTS driver_id_type TEXT;
ALTER TABLE vehicle ADD COLUMN IF NOT EXISTS driver_id_number TEXT;
ALTER TABLE vehicle ADD COLUMN IF NOT EXISTS vehicle_length TEXT;
