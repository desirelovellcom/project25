-- Energy Cost Analysis System - Initial Database Schema
-- This script creates all the core tables for the energy cost analysis system

-- Sources table for tracking crawled websites and data sources
CREATE TABLE sources (
  id BIGSERIAL PRIMARY KEY,
  url TEXT NOT NULL UNIQUE,
  domain TEXT NOT NULL,
  robots_ok BOOLEAN DEFAULT TRUE,
  license TEXT,
  first_seen TIMESTAMPTZ DEFAULT NOW(),
  last_crawled TIMESTAMPTZ,
  content_hash TEXT
);

-- Documents table for storing processed content from sources
CREATE TABLE documents (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT REFERENCES sources(id),
  title TEXT,
  published_at TIMESTAMPTZ,
  snippet TEXT,
  raw_s3_uri TEXT NOT NULL,
  embedding VECTOR(1536),
  tags TEXT[]
);

-- Entities table for energy system components (Tesla products, competitors, etc.)
CREATE TABLE entities (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT CHECK (type IN ('pv','battery','inverter','thermal','wind','hydro','policy','tariff')),
  manufacturer TEXT,
  model TEXT,
  version TEXT,
  UNIQUE(name, manufacturer, model, version)
);

-- Facts table for storing extracted technical specifications and metrics
CREATE TABLE facts (
  id BIGSERIAL PRIMARY KEY,
  entity_id BIGINT REFERENCES entities(id),
  document_id BIGINT REFERENCES documents(id),
  metric TEXT,              -- e.g. 'capex_per_kw', 'round_trip_efficiency'
  value DOUBLE PRECISION,
  unit TEXT,
  span_excerpt TEXT,
  quality_score DOUBLE PRECISION DEFAULT 0.5,
  extracted_at TIMESTAMPTZ DEFAULT NOW()
);

-- Prices table for tracking current market pricing
CREATE TABLE prices (
  id BIGSERIAL PRIMARY KEY,
  entity_id BIGINT REFERENCES entities(id),
  region TEXT,
  price_value DOUBLE PRECISION,
  currency TEXT DEFAULT 'USD',
  basis TEXT,               -- 'installed', 'ex-factory', 'quote'
  vendor_url TEXT,
  valid_from DATE,
  valid_to DATE
);

-- Assumptions table for economic modeling parameters
CREATE TABLE assumptions (
  id BIGSERIAL PRIMARY KEY,
  name TEXT UNIQUE,
  value DOUBLE PRECISION,
  unit TEXT,
  source_document_id BIGINT REFERENCES documents(id)
);

-- Scenarios table for different analysis contexts
CREATE TABLE scenarios (
  id BIGSERIAL PRIMARY KEY,
  name TEXT,
  use_case TEXT CHECK (use_case IN ('residential','commercial','utility')),
  region TEXT,
  load_profile JSONB,
  financing JSONB,
  incentives JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Results table for computed LCOE values
CREATE TABLE results_lcoe (
  id BIGSERIAL PRIMARY KEY,
  scenario_id BIGINT REFERENCES scenarios(id),
  entity_id BIGINT REFERENCES entities(id),
  lcoe_usd_per_kwh DOUBLE PRECISION,
  breakdown JSONB,
  computed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(scenario_id, entity_id)
);

-- Create indexes for performance
CREATE INDEX idx_sources_domain ON sources(domain);
CREATE INDEX idx_documents_source_id ON documents(source_id);
CREATE INDEX idx_facts_entity_id ON facts(entity_id);
CREATE INDEX idx_facts_document_id ON facts(document_id);
CREATE INDEX idx_prices_entity_id ON prices(entity_id);
CREATE INDEX idx_results_scenario_id ON results_lcoe(scenario_id);
