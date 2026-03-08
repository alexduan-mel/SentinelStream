ALTER TABLE llm_analyses
  ADD COLUMN IF NOT EXISTS analysis_job_id BIGINT NULL;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.table_constraints tc
    WHERE tc.table_name = 'llm_analyses'
      AND tc.constraint_type = 'FOREIGN KEY'
      AND tc.constraint_name = 'fk_llm_analyses_job_id'
  ) THEN
    ALTER TABLE llm_analyses
      ADD CONSTRAINT fk_llm_analyses_job_id
      FOREIGN KEY (analysis_job_id)
      REFERENCES analysis_jobs(id)
      ON DELETE SET NULL;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_analysis_job_id ON llm_analyses (analysis_job_id);

COMMENT ON COLUMN llm_analyses.analysis_job_id IS 'FK to analysis_jobs.id (nullable)';
