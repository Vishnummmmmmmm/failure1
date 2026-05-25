-- PulseSphere Complete Schema v1
-- Run in: Supabase Dashboard → SQL Editor

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ORGS
CREATE TABLE IF NOT EXISTS orgs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL,
  plan text DEFAULT 'starter' CHECK (plan IN ('starter','professional','agency','enterprise')),
  white_label_logo_url text,
  created_at timestamptz DEFAULT now()
);

-- BRANDS
CREATE TABLE IF NOT EXISTS brands (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id uuid REFERENCES orgs(id) ON DELETE CASCADE,
  name text NOT NULL,
  keywords text[] NOT NULL DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

-- POSTS
CREATE TABLE IF NOT EXISTS posts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id uuid REFERENCES brands(id) ON DELETE CASCADE,
  source text NOT NULL CHECK (source IN ('google','reddit','twitter','instagram','facebook','threads','news','rss')),
  content text NOT NULL,
  author text,
  url text,
  emotion_scores jsonb DEFAULT '{}',
  is_fake_news bool DEFAULT false,
  is_bot_generated bool DEFAULT false,
  crisis_category text,
  cvi_contribution float DEFAULT 0,
  ingested_at timestamptz DEFAULT now()
);

-- CVI_SNAPSHOTS
CREATE TABLE IF NOT EXISTS cvi_snapshots (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id uuid REFERENCES brands(id) ON DELETE CASCADE,
  score float NOT NULL CHECK (score >= 0 AND score <= 100),
  level text NOT NULL CHECK (level IN ('LOW','WATCH','MEDIUM','HIGH','CRITICAL')),
  neg_rate float DEFAULT 0,
  velocity float DEFAULT 1,
  spike_factor float DEFAULT 1,
  is_anomaly bool DEFAULT false,
  recorded_at timestamptz DEFAULT now()
);
CREATE INDEX idx_cvi_brand_time ON cvi_snapshots(brand_id, recorded_at DESC);

-- CRISIS_MEMORY
CREATE TABLE IF NOT EXISTS crisis_memory (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id uuid REFERENCES brands(id),
  crisis_label text,
  cvi_t_minus_30 float,
  cvi_t_minus_15 float,
  cvi_t_0 float,
  cvi_t_plus_60 float,
  peak_at timestamptz DEFAULT now()
);

-- ALERTS
CREATE TABLE IF NOT EXISTS alerts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id uuid REFERENCES brands(id),
  severity text NOT NULL CHECK (severity IN ('WATCH','MEDIUM','HIGH','CRITICAL')),
  cvi_score float NOT NULL,
  triggered_at timestamptz DEFAULT now(),
  resolved_at timestamptz,
  channels_notified text[] DEFAULT '{}'
);

-- PLAYBOOKS
CREATE TABLE IF NOT EXISTS playbooks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  brand_id uuid REFERENCES brands(id),
  alert_id uuid REFERENCES alerts(id),
  actions jsonb DEFAULT '[]',
  press_statement text,
  rating int CHECK (rating IN (0,1)),
  generated_at timestamptz DEFAULT now()
);

-- DEMO ORG SEED
INSERT INTO orgs (id, name, plan)
VALUES ('00000000-0000-0000-0000-000000000001', 'Demo Org', 'agency')
ON CONFLICT DO NOTHING;

-- ENABLE REALTIME FOR cvi_snapshots
alter publication supabase_realtime add table cvi_snapshots;
