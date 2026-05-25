-- White-label branding columns
ALTER TABLE orgs ADD COLUMN IF NOT EXISTS white_label_logo_url  text;
ALTER TABLE orgs ADD COLUMN IF NOT EXISTS accent_color          text DEFAULT '#00E5FF';
ALTER TABLE orgs ADD COLUMN IF NOT EXISTS org_display_name      text;

-- Supabase Storage bucket for logos (run once)
-- Do this in Dashboard → Storage → New bucket → name: org-logos → public: true
-- OR run:
INSERT INTO storage.buckets (id, name, public)
VALUES ('org-logos', 'org-logos', true)
ON CONFLICT DO NOTHING;
