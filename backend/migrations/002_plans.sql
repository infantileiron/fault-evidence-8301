-- 002: ObservationPlan aggregate (budgeted adaptive observation plans).
-- Fresh databases are created by SQLAlchemy metadata; apply this reviewed
-- incremental migration only to existing production databases.
CREATE TABLE IF NOT EXISTS plans (
  id VARCHAR(36) NOT NULL PRIMARY KEY,
  created_at DATETIME NOT NULL,
  case_id VARCHAR(36) NOT NULL,
  budget INT NOT NULL,
  costs JSON NOT NULL,
  status VARCHAR(20) NOT NULL,
  result JSON NOT NULL,
  error TEXT NOT NULL,
  baseline_entropy DOUBLE NULL,
  expected_remaining_entropy DOUBLE NULL,
  FOREIGN KEY (case_id) REFERENCES cases(id)
);
