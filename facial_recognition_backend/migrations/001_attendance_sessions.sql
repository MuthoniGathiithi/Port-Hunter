-- Required columns and indexes for attendance + registration flow.
-- Safe to run multiple times.

ALTER TABLE IF EXISTS students
  ADD COLUMN IF NOT EXISTS embeddings jsonb DEFAULT '[]'::jsonb;

ALTER TABLE IF EXISTS units
  ADD COLUMN IF NOT EXISTS registration_token text;

ALTER TABLE IF EXISTS attendance_sessions
  ADD COLUMN IF NOT EXISTS totals jsonb DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS present jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS absent jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS unknown jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS classroom_photos jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS status text DEFAULT 'processing',
  ADD COLUMN IF NOT EXISTS session_date timestamptz DEFAULT now();

CREATE INDEX IF NOT EXISTS idx_students_unit_id ON students (unit_id);
CREATE INDEX IF NOT EXISTS idx_students_admission ON students (admission_number);
CREATE INDEX IF NOT EXISTS idx_units_lecturer_id ON units (lecturer_id);
CREATE INDEX IF NOT EXISTS idx_attendance_unit_id ON attendance_sessions (unit_id);
CREATE INDEX IF NOT EXISTS idx_attendance_session_date ON attendance_sessions (session_date);
