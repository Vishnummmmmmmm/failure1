-- PulseSphere RLS Policies v1
-- Run AFTER schema.sql
-- Requires Supabase Auth enabled in project settings

-- ── org_members join table ────────────────────────────────
CREATE TABLE IF NOT EXISTS org_members (
  id         uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id     uuid REFERENCES orgs(id) ON DELETE CASCADE,
  user_id    uuid NOT NULL,  -- references auth.users.id
  role       text DEFAULT 'member' CHECK (role IN ('owner','admin','member')),
  invited_at timestamptz DEFAULT now(),
  UNIQUE(org_id, user_id)
);

-- ── Enable RLS on all tables ──────────────────────────────
ALTER TABLE orgs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE brands        ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE cvi_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE playbooks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE crisis_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_members   ENABLE ROW LEVEL SECURITY;

-- ── Helper: is current user a member of this org? ─────────
CREATE OR REPLACE FUNCTION is_org_member(org uuid)
RETURNS boolean LANGUAGE sql SECURITY DEFINER AS $$
  SELECT EXISTS (
    SELECT 1 FROM org_members
    WHERE org_id = org AND user_id = auth.uid()
  );
$$;

-- ── orgs: members can read their org ─────────────────────
DROP POLICY IF EXISTS "orgs_select" ON orgs;
CREATE POLICY "orgs_select" ON orgs
  FOR SELECT USING (is_org_member(id));

-- ── brands: scoped to org ────────────────────────────────
DROP POLICY IF EXISTS "brands_select" ON brands;
CREATE POLICY "brands_select" ON brands
  FOR SELECT USING (is_org_member(org_id));

DROP POLICY IF EXISTS "brands_insert" ON brands;
CREATE POLICY "brands_insert" ON brands
  FOR INSERT WITH CHECK (is_org_member(org_id));

DROP POLICY IF EXISTS "brands_delete" ON brands;
CREATE POLICY "brands_delete" ON brands
  FOR DELETE USING (is_org_member(org_id));

-- ── posts: via brand → org ───────────────────────────────
DROP POLICY IF EXISTS "posts_select" ON posts;
CREATE POLICY "posts_select" ON posts
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = posts.brand_id AND is_org_member(b.org_id)
    )
  );

DROP POLICY IF EXISTS "posts_insert" ON posts;
CREATE POLICY "posts_insert" ON posts
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = posts.brand_id AND is_org_member(b.org_id)
    )
  );

-- ── cvi_snapshots: via brand → org ───────────────────────
DROP POLICY IF EXISTS "cvi_select" ON cvi_snapshots;
CREATE POLICY "cvi_select" ON cvi_snapshots
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = cvi_snapshots.brand_id AND is_org_member(b.org_id)
    )
  );

DROP POLICY IF EXISTS "cvi_insert" ON cvi_snapshots;
CREATE POLICY "cvi_insert" ON cvi_snapshots
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = cvi_snapshots.brand_id AND is_org_member(b.org_id)
    )
  );

-- ── alerts: via brand → org ──────────────────────────────
DROP POLICY IF EXISTS "alerts_select" ON alerts;
CREATE POLICY "alerts_select" ON alerts
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = alerts.brand_id AND is_org_member(b.org_id)
    )
  );

-- ── playbooks: via brand → org ───────────────────────────
DROP POLICY IF EXISTS "playbooks_select" ON playbooks;
CREATE POLICY "playbooks_select" ON playbooks
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = playbooks.brand_id AND is_org_member(b.org_id)
    )
  );

DROP POLICY IF EXISTS "playbooks_insert" ON playbooks;
CREATE POLICY "playbooks_insert" ON playbooks
  FOR INSERT WITH CHECK (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = playbooks.brand_id AND is_org_member(b.org_id)
    )
  );

DROP POLICY IF EXISTS "playbooks_update" ON playbooks;
CREATE POLICY "playbooks_update" ON playbooks
  FOR UPDATE USING (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = playbooks.brand_id AND is_org_member(b.org_id)
    )
  );

-- ── crisis_memory: via brand → org ───────────────────────
DROP POLICY IF EXISTS "crisis_memory_select" ON crisis_memory;
CREATE POLICY "crisis_memory_select" ON crisis_memory
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM brands b
      WHERE b.id = crisis_memory.brand_id AND is_org_member(b.org_id)
    )
  );

-- ── org_members: members see own rows ────────────────────
DROP POLICY IF EXISTS "org_members_select" ON org_members;
CREATE POLICY "org_members_select" ON org_members
  FOR SELECT USING (user_id = auth.uid());

-- ── Service role bypasses RLS (backend uses service key) ─
-- Backend FastAPI uses SUPABASE_SERVICE_KEY which bypasses all RLS.
-- Frontend uses SUPABASE_ANON_KEY which is subject to RLS.
-- This means: all backend writes are unrestricted, all frontend reads are tenant-scoped.

-- ── Demo org: add yourself as owner ─────────────────────
-- Replace <YOUR_AUTH_USER_UUID> with your auth.users id after first login
-- INSERT INTO org_members (org_id, user_id, role)
-- VALUES ('00000000-0000-0000-0000-000000000001', '<YOUR_AUTH_USER_UUID>', 'owner')
-- ON CONFLICT DO NOTHING;
