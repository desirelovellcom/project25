-- Create ops_audit table for admin action logging
CREATE TABLE IF NOT EXISTS ops_audit (
    id BIGSERIAL PRIMARY KEY,
    user_email TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL,
    result JSONB NOT NULL,
    ts TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_ops_audit_ts ON ops_audit(ts DESC);
CREATE INDEX IF NOT EXISTS idx_ops_audit_user ON ops_audit(user_email);
CREATE INDEX IF NOT EXISTS idx_ops_audit_action ON ops_audit(action);

-- Insert sample audit entries
INSERT INTO ops_audit (user_email, action, target, result) VALUES
('admin@tesla.com', 'vacuum_analyze', 'database', '{"status": "completed", "tables_processed": 12}'),
('admin@tesla.com', 'scale_api', 'kubernetes', '{"status": "scaled", "replicas": 3, "target": "api"}'),
('ops@tesla.com', 'backup_snapshot', 'database', '{"status": "completed", "backup_id": "backup_20240115_030000"}');
