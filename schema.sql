CREATE TABLE IF NOT EXISTS memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  memory_type STRING NOT NULL,
  content STRING NOT NULL,
  embedding VECTOR(1024) NOT NULL,
  confidence FLOAT8 NOT NULL DEFAULT 0.5,
  source STRING,
  status STRING NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  valid_until TIMESTAMPTZ NULL,
  supersedes UUID NULL
);

CREATE TABLE IF NOT EXISTS workflows (
  workflow_id UUID PRIMARY KEY,
  status STRING NOT NULL,
  incident STRING NOT NULL,
  last_completed_step INT NOT NULL DEFAULT 0,
  total_steps INT NOT NULL DEFAULT 4,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS workflow_steps (
  workflow_id UUID NOT NULL,
  step_number INT NOT NULL,
  name STRING NOT NULL,
  status STRING NOT NULL,
  result STRING,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workflow_id, step_number)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id UUID,
  action STRING NOT NULL,
  details STRING,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE VECTOR INDEX IF NOT EXISTS memories_embedding_idx ON memories (embedding);
