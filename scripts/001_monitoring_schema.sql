-- Core monitoring platform database schema
-- Infrastructure and service monitoring tables

-- Organizations and users
CREATE TABLE organizations (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    organization_id BIGINT REFERENCES organizations(id),
    role TEXT CHECK (role IN ('admin', 'user', 'viewer')) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ
);

-- Infrastructure monitoring
CREATE TABLE hosts (
    id BIGSERIAL PRIMARY KEY,
    hostname TEXT NOT NULL,
    ip_address INET,
    organization_id BIGINT REFERENCES organizations(id),
    tags JSONB DEFAULT '{}',
    agent_version TEXT,
    os_type TEXT,
    os_version TEXT,
    cpu_cores INTEGER,
    memory_gb DECIMAL,
    disk_gb DECIMAL,
    status TEXT CHECK (status IN ('online', 'offline', 'warning', 'critical')) DEFAULT 'offline',
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE services (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    host_id BIGINT REFERENCES hosts(id),
    organization_id BIGINT REFERENCES organizations(id),
    service_type TEXT, -- web, database, cache, etc.
    port INTEGER,
    health_check_url TEXT,
    status TEXT CHECK (status IN ('running', 'stopped', 'warning', 'critical')) DEFAULT 'stopped',
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Time-series metrics storage
CREATE TABLE metrics (
    id BIGSERIAL PRIMARY KEY,
    host_id BIGINT REFERENCES hosts(id),
    service_id BIGINT REFERENCES services(id),
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for time-series queries
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX idx_metrics_host_metric ON metrics(host_id, metric_name, timestamp DESC);
CREATE INDEX idx_metrics_service_metric ON metrics(service_id, metric_name, timestamp DESC);

-- Log aggregation
CREATE TABLE logs (
    id BIGSERIAL PRIMARY KEY,
    host_id BIGINT REFERENCES hosts(id),
    service_id BIGINT REFERENCES services(id),
    level TEXT CHECK (level IN ('debug', 'info', 'warn', 'error', 'fatal')),
    message TEXT NOT NULL,
    source TEXT, -- application, system, etc.
    tags JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_level ON logs(level, timestamp DESC);
CREATE INDEX idx_logs_host ON logs(host_id, timestamp DESC);

-- Alerting system
CREATE TABLE alert_rules (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    organization_id BIGINT REFERENCES organizations(id),
    metric_name TEXT NOT NULL,
    condition TEXT NOT NULL, -- >, <, =, etc.
    threshold DOUBLE PRECISION NOT NULL,
    duration_minutes INTEGER DEFAULT 5,
    severity TEXT CHECK (severity IN ('info', 'warning', 'critical')) DEFAULT 'warning',
    enabled BOOLEAN DEFAULT true,
    tags JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    rule_id BIGINT REFERENCES alert_rules(id),
    host_id BIGINT REFERENCES hosts(id),
    service_id BIGINT REFERENCES services(id),
    status TEXT CHECK (status IN ('firing', 'resolved')) DEFAULT 'firing',
    message TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('info', 'warning', 'critical')),
    fired_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Distributed tracing
CREATE TABLE traces (
    id BIGSERIAL PRIMARY KEY,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    operation_name TEXT NOT NULL,
    service_name TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    duration_ms INTEGER NOT NULL,
    tags JSONB DEFAULT '{}',
    logs JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_traces_trace_id ON traces(trace_id);
CREATE INDEX idx_traces_service ON traces(service_name, start_time DESC);

-- Dashboards and visualization
CREATE TABLE dashboards (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    organization_id BIGINT REFERENCES organizations(id),
    created_by BIGINT REFERENCES users(id),
    config JSONB NOT NULL, -- dashboard layout and widgets
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
