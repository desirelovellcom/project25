# Energy Cost Analysis System

A comprehensive energy cost analysis system that discovers, normalizes, and analyzes energy cost data with LCOE/LCOS computation capabilities.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Make (optional, for convenience commands)

### Local Development

1. **Start the development environment:**
   \`\`\`bash
   make dev-up
   # or
   docker compose up --build -d
   \`\`\`

2. **Verify services are running:**
   - Database: `localhost:5432`
   - Redis: `localhost:6379` 
   - OpenSearch: `http://localhost:9200`
   - MinIO Console: `http://localhost:9001`

3. **Run demo seed data:**
   \`\`\`bash
   make seed-demo
   \`\`\`

## 🏗️ Architecture

### Monorepo Structure
\`\`\`
energy-cost-system/
├── apps/
│   ├── web/                # Next.js + Tailwind (UI)
│   ├── api/                # FastAPI (REST) + Celery worker
│   └── scheduler/          # Beat/cron, pipelines as DAGs
├── packages/
│   ├── lcoe/               # Pure python LCOE/LCOS lib
│   ├── extraction/         # Parsers, NER, unit normalization
│   └── common/             # Types, config, observability
├── infra/
│   ├── terraform/          # AWS infrastructure
│   ├── k8s/                # Kubernetes manifests
│   └── docker/             # Container definitions
├── data/
│   ├── seeds/              # Initial data and assumptions
│   └── notebooks/          # Analysis notebooks
└── ops/
    ├── runbooks/           # Operational procedures
    └── dashboards/         # Grafana dashboards
\`\`\`

### Core Services
- **API**: FastAPI with OpenAPI documentation
- **Worker**: Celery for background processing
- **Database**: PostgreSQL with pgvector extension
- **Search**: OpenSearch for document discovery
- **Storage**: S3-compatible object store (MinIO locally)
- **Cache**: Redis for task queue and caching

## 🔄 Data Pipeline

The system follows a "Scan→Extract→Compute→Rank" pipeline:

1. **Seed Search**: Discover energy-related content
2. **Fetch & Store**: Crawl URLs respecting robots.txt
3. **Extract Facts**: Parse documents for technical specifications
4. **Normalize Data**: Standardize units and deduplicate
5. **Compute LCOE/LCOS**: Calculate levelized costs
6. **Generate Rankings**: Rank solutions by scenario

## 🔧 Development Commands

\`\`\`bash
make dev-up        # Start development environment
make dev-down      # Stop development environment
make seed-demo     # Run demo data pipeline
make test          # Run test suite
make lint          # Run linting and formatting
make clean         # Clean up environment
make db-reset      # Reset database (destroys data!)
\`\`\`

## 📊 Energy Product Support

Comprehensive support for energy products across all manufacturers:
- **Solar**: Panels, rooftop systems, utility-scale installations
- **Storage**: Residential batteries, commercial systems, utility-scale storage
- **Metrics**: LCOE, LCOS, capacity factors, efficiency ratings
- **Comparisons**: Multi-vendor analysis with citations and data provenance

## 🔒 Security & Compliance

- Respects robots.txt and site terms
- Rate limiting per domain
- No PII collection
- Citations and timestamps for all data
- Immutable infrastructure patterns

## 📈 Observability

- OpenTelemetry tracing
- Prometheus metrics
- Grafana dashboards
- Real-time pipeline monitoring
- SLA tracking and alerting

## 🚀 Deployment

- **Local**: Docker Compose
- **Cloud**: Terraform + Kubernetes
- **Rollouts**: Blue/green with health checks
- **Rollback**: < 2 minutes with versioned datasets

## 📝 License

This project follows enterprise-grade principles: vertical integration, telemetry-first, and deterministic builds.
