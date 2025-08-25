"""
Celery tasks for the energy cost analysis pipeline
"""

from celery import Celery
import os
import asyncio
import asyncpg
import httpx
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import hashlib
from datetime import datetime
import json
from celery.schedules import crontab

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "energy_cost_tasks",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

async def get_db_connection():
    """Get database connection for async tasks"""
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:dev_password@localhost:5432/energy_cost")
    return await asyncpg.connect(database_url)

def check_robots_txt(url: str) -> bool:
    """Check if URL is allowed by robots.txt"""
    try:
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        return rp.can_fetch("*", url)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        return True  # Allow if robots.txt check fails

@celery_app.task(bind=True, name="seed_search")
def seed_search_task(self, query_set: list):
    """
    Task: Discover URLs through search queries
    Input: List of search queries
    Output: URLs stored in sources table
    """
    try:
        logger.info(f"Starting seed search with queries: {query_set}")
        
        # This would integrate with search APIs (Google, Bing, etc.)
        # For now, we'll use a mock implementation with known energy sites
        mock_urls = [
            "https://www.nrel.gov/analysis/tech-lcoe-documentation.html",
            "https://www.eia.gov/electricity/generatorcosts/",
            "https://www.irena.org/costs",
            "https://www.lazard.com/perspective/levelized-cost-of-energy-levelized-cost-of-storage-and-levelized-cost-of-hydrogen/",
            "https://www.energy.gov/eere/solar/solar-energy-technologies-office",
            "https://www.energy.gov/oe/activities/technology-development/grid-modernization-and-smart-grid/role-energy-storage",
        ]
        
        async def store_urls():
            conn = await get_db_connection()
            try:
                for url in mock_urls:
                    domain = urlparse(url).netloc
                    robots_ok = check_robots_txt(url)
                    
                    await conn.execute("""
                        INSERT INTO sources (url, domain, robots_ok, first_seen)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (url) DO NOTHING
                    """, url, domain, robots_ok, datetime.utcnow())
                    
                logger.info(f"Stored {len(mock_urls)} URLs from seed search")
            finally:
                await conn.close()
        
        # Run async function
        asyncio.run(store_urls())
        
        return {
            "status": "completed",
            "urls_found": len(mock_urls),
            "queries_processed": len(query_set)
        }
        
    except Exception as e:
        logger.error(f"Seed search task failed: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name="fetch_url")
def fetch_url_task(self, url: str):
    """
    Task: Fetch and store raw content from URL
    Input: URL string
    Output: Document stored in documents table, raw content in S3
    """
    try:
        logger.info(f"Fetching URL: {url}")
        
        async def fetch_and_store():
            conn = await get_db_connection()
            try:
                # Check if URL is allowed by robots.txt
                if not check_robots_txt(url):
                    logger.warning(f"URL blocked by robots.txt: {url}")
                    return {"status": "blocked", "url": url}
                
                # Fetch content
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    
                    content = response.text
                    content_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Store raw content (mock S3 storage for now)
                    s3_uri = f"s3://energy-artifacts/raw/{content_hash}.html"
                    
                    # Extract basic metadata
                    title = "Unknown"
                    if "<title>" in content:
                        start = content.find("<title>") + 7
                        end = content.find("</title>", start)
                        if end > start:
                            title = content[start:end].strip()
                    
                    # Get source_id
                    source_row = await conn.fetchrow("SELECT id FROM sources WHERE url = $1", url)
                    if not source_row:
                        logger.error(f"Source not found for URL: {url}")
                        return {"status": "error", "message": "Source not found"}
                    
                    source_id = source_row['id']
                    
                    # Store document
                    await conn.execute("""
                        INSERT INTO documents (source_id, title, raw_s3_uri, snippet)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT DO NOTHING
                    """, source_id, title, s3_uri, content[:500])
                    
                    # Update source last_crawled
                    await conn.execute("""
                        UPDATE sources 
                        SET last_crawled = $1, content_hash = $2
                        WHERE url = $3
                    """, datetime.utcnow(), content_hash, url)
                    
                    logger.info(f"Successfully fetched and stored: {url}")
                    return {"status": "completed", "url": url, "content_length": len(content)}
                    
            finally:
                await conn.close()
        
        return asyncio.run(fetch_and_store())
        
    except Exception as e:
        logger.error(f"Fetch URL task failed for {url}: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name="parse_document")
def parse_document_task(self, doc_id: int):
    """
    Task: Parse document content and extract metadata
    Input: Document ID
    Output: Enhanced document metadata
    """
    try:
        logger.info(f"Parsing document ID: {doc_id}")
        
        # This would use trafilatura or similar for content extraction
        # Mock implementation for now
        
        return {"status": "completed", "doc_id": doc_id}
        
    except Exception as e:
        logger.error(f"Parse document task failed for {doc_id}: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name="extract_facts")
def extract_facts_task(self):
    """
    Task: Extract facts from all unprocessed documents
    Input: None (processes all unprocessed docs)
    Output: Facts stored in facts table
    """
    try:
        logger.info("Starting fact extraction from documents")
        
        async def extract_facts():
            conn = await get_db_connection()
            try:
                # Get unprocessed documents
                docs = await conn.fetch("""
                    SELECT d.id, d.title, d.snippet, s.url
                    FROM documents d
                    JOIN sources s ON d.source_id = s.id
                    WHERE d.id NOT IN (SELECT DISTINCT document_id FROM facts WHERE document_id IS NOT NULL)
                    LIMIT 10
                """)
                
                facts_extracted = 0
                
                for doc in docs:
                    # Mock fact extraction - in reality would use NLP/LLM
                    mock_facts = [
                        {
                            "metric": "capacity_kwh",
                            "value": 13.5,
                            "unit": "kWh",
                            "span_excerpt": "13.5 kWh usable capacity"
                        }
                    ]
                    
                    for fact in mock_facts:
                        await conn.execute("""
                            INSERT INTO facts (document_id, metric, value, unit, span_excerpt, quality_score)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, doc['id'], fact['metric'], fact['value'], fact['unit'], 
                             fact['span_excerpt'], 0.8)
                        facts_extracted += 1
                
                logger.info(f"Extracted {facts_extracted} facts from {len(docs)} documents")
                return {"status": "completed", "facts_extracted": facts_extracted}
                
            finally:
                await conn.close()
        
        return asyncio.run(extract_facts())
        
    except Exception as e:
        logger.error(f"Extract facts task failed: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name="compute_lcoe")
def compute_lcoe_task(self, scenario_id: int):
    """
    Task: Compute LCOE/LCOS for all entities in a scenario
    Input: Scenario ID
    Output: Results stored in results_lcoe table
    """
    try:
        logger.info(f"Computing LCOE for scenario: {scenario_id}")
        
        async def compute_lcoe():
            conn = await get_db_connection()
            try:
                # Get all entities
                entities = await conn.fetch("SELECT id, name, type FROM entities")
                
                results_computed = 0
                
                for entity in entities:
                    # Mock LCOE computation - would use packages/lcoe library
                    mock_lcoe = 0.12  # $0.12/kWh
                    mock_breakdown = {
                        "capex": 0.08,
                        "opex": 0.02,
                        "fuel": 0.02,
                        "discount_rate": 0.07,
                        "lifetime_years": 25
                    }
                    
                    await conn.execute("""
                        INSERT INTO results_lcoe (scenario_id, entity_id, lcoe_usd_per_kwh, breakdown)
                        VALUES ($1, $2, $3, $4)
                        ON CONFLICT (scenario_id, entity_id) 
                        DO UPDATE SET 
                            lcoe_usd_per_kwh = EXCLUDED.lcoe_usd_per_kwh,
                            breakdown = EXCLUDED.breakdown,
                            computed_at = NOW()
                    """, scenario_id, entity['id'], mock_lcoe, json.dumps(mock_breakdown))
                    
                    results_computed += 1
                
                logger.info(f"Computed LCOE for {results_computed} entities")
                return {"status": "completed", "results_computed": results_computed}
                
            finally:
                await conn.close()
        
        return asyncio.run(compute_lcoe())
        
    except Exception as e:
        logger.error(f"Compute LCOE task failed for scenario {scenario_id}: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name="publish_rankings")
def publish_rankings_task(self, scenario_id: int):
    """
    Task: Publish rankings to cache and emit metrics
    Input: Scenario ID
    Output: Cached rankings, metrics emitted
    """
    try:
        logger.info(f"Publishing rankings for scenario: {scenario_id}")
        
        # This would cache results in Redis and emit Prometheus metrics
        # Mock implementation for now
        
        return {"status": "completed", "scenario_id": scenario_id}
        
    except Exception as e:
        logger.error(f"Publish rankings task failed for scenario {scenario_id}: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.task(bind=True, name="vacuum_analyze")
def vacuum_analyze_task(self):
    """
    Task: Run VACUUM ANALYZE on all tables for database maintenance
    Input: None
    Output: Database optimization completed
    """
    try:
        logger.info("Starting database vacuum analyze maintenance")
        
        async def vacuum_analyze():
            conn = await get_db_connection()
            try:
                # Get all user tables
                tables = await conn.fetch("""
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                """)
                
                tables_processed = 0
                
                for table in tables:
                    table_name = f"{table['schemaname']}.{table['tablename']}"
                    logger.info(f"Running VACUUM ANALYZE on {table_name}")
                    
                    # Run VACUUM ANALYZE (note: this requires autocommit mode)
                    await conn.execute(f"VACUUM ANALYZE {table_name}")
                    tables_processed += 1
                
                logger.info(f"Completed VACUUM ANALYZE on {tables_processed} tables")
                return {"status": "completed", "tables_processed": tables_processed}
                
            finally:
                await conn.close()
        
        return asyncio.run(vacuum_analyze())
        
    except Exception as e:
        logger.error(f"Vacuum analyze task failed: {e}")
        self.retry(countdown=300, max_retries=2)  # Retry after 5 minutes

@celery_app.task(bind=True, name="backup_database")
def backup_database_task(self):
    """
    Task: Create database backup snapshot
    Input: None
    Output: Backup created and stored
    """
    try:
        logger.info("Starting database backup")
        
        # In production, this would trigger AWS RDS snapshot or pg_dump to S3
        backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Mock backup process
        import time
        time.sleep(5)  # Simulate backup time
        
        logger.info(f"Database backup completed: {backup_id}")
        return {"status": "completed", "backup_id": backup_id}
        
    except Exception as e:
        logger.error(f"Database backup task failed: {e}")
        self.retry(countdown=600, max_retries=1)  # Retry after 10 minutes

@celery_app.task(bind=True, name="collect_metrics")
def collect_metrics_task(self):
    """
    Task: Collect and emit system metrics to Prometheus
    Input: None
    Output: Metrics collected and emitted
    """
    try:
        logger.info("Collecting system metrics")
        
        async def collect_metrics():
            conn = await get_db_connection()
            try:
                # Database metrics
                db_metrics = await conn.fetchrow("""
                    SELECT 
                        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                        (SELECT count(*) FROM sources) as total_sources,
                        (SELECT count(*) FROM documents) as total_documents,
                        (SELECT count(*) FROM facts) as total_facts,
                        (SELECT count(*) FROM results_lcoe) as total_results
                """)
                
                # Data freshness metrics
                freshness = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) FILTER (WHERE computed_at > NOW() - INTERVAL '7 days') as fresh_results,
                        COUNT(*) FILTER (WHERE computed_at > NOW() - INTERVAL '30 days') as recent_results,
                        COUNT(*) as total_results
                    FROM results_lcoe
                """)
                
                metrics = {
                    "database": dict(db_metrics),
                    "freshness": dict(freshness),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # In production, emit to Prometheus here
                logger.info(f"Collected metrics: {metrics}")
                return {"status": "completed", "metrics": metrics}
                
            finally:
                await conn.close()
        
        return asyncio.run(collect_metrics())
        
    except Exception as e:
        logger.error(f"Collect metrics task failed: {e}")
        self.retry(countdown=60, max_retries=3)

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks for maintenance and monitoring"""
    
    # Run vacuum analyze weekly (Sunday at 2 AM UTC)
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_week=0),
        vacuum_analyze_task.s(),
        name='weekly-vacuum-analyze'
    )
    
    # Collect metrics every 5 minutes
    sender.add_periodic_task(
        60.0 * 5,  # 5 minutes
        collect_metrics_task.s(),
        name='collect-metrics'
    )
    
    # Daily backup at 3 AM UTC
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        backup_database_task.s(),
        name='daily-backup'
    )
