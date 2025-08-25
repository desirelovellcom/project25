"""
Energy Cost Analysis API - Main FastAPI Application
Comprehensive energy cost analysis with LCOE/LCOS computation
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import List, Optional
import logging

from .database import get_db, Database
from .models import (
    Entity, EntityCreate, EntityResponse,
    IngestRequest, ComputeRequest, 
    RankingResponse, HealthResponse
)
from .tasks import (
    seed_search_task, fetch_url_task, parse_document_task,
    extract_facts_task, compute_lcoe_task, publish_rankings_task
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Energy Cost Analysis API",
    description="Comprehensive energy cost analysis with LCOE/LCOS computation",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    try:
        # Test database connection
        async with get_db() as db:
            await db.execute("SELECT 1")
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            services={
                "database": "healthy",
                "redis": "healthy",
                "opensearch": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.get("/api/entities", response_model=List[EntityResponse])
async def list_entities(
    q: Optional[str] = Query(None, description="Search query for entities"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    db: Database = Depends(get_db)
):
    """List and search energy system entities (solar, storage, and hybrid systems from all manufacturers)"""
    try:
        query = """
            SELECT id, name, type, manufacturer, model, version
            FROM entities
            WHERE 1=1
        """
        params = []
        
        if q:
            query += " AND (name ILIKE $%d OR manufacturer ILIKE $%d)" % (len(params)+1, len(params)+2)
            params.extend([f"%{q}%", f"%{q}%"])
        
        if entity_type:
            query += " AND type = $%d" % (len(params)+1)
            params.append(entity_type)
            
        if manufacturer:
            query += " AND manufacturer ILIKE $%d" % (len(params)+1)
            params.append(f"%{manufacturer}%")
        
        query += " ORDER BY manufacturer, name"
        
        rows = await db.fetch_all(query, *params)
        return [EntityResponse(**dict(row)) for row in rows]
        
    except Exception as e:
        logger.error(f"Error listing entities: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve entities")

@app.post("/api/entities", response_model=EntityResponse, status_code=201)
async def create_entity(
    entity: EntityCreate,
    db: Database = Depends(get_db)
):
    """Create a new energy system entity"""
    try:
        query = """
            INSERT INTO entities (name, type, manufacturer, model, version)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, name, type, manufacturer, model, version
        """
        
        row = await db.fetch_one(
            query, 
            entity.name, entity.type, entity.manufacturer, 
            entity.model, entity.version
        )
        
        return EntityResponse(**dict(row))
        
    except Exception as e:
        logger.error(f"Error creating entity: {e}")
        raise HTTPException(status_code=500, detail="Failed to create entity")

@app.post("/api/ingest/search", status_code=202)
async def trigger_search_ingest(request: IngestRequest):
    """Trigger seed search for energy-related content"""
    try:
        # Queue search task
        task = seed_search_task.delay(request.query_set)
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Search ingest queued",
                "task_id": task.id,
                "query_set": request.query_set
            }
        )
    except Exception as e:
        logger.error(f"Error queuing search ingest: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue search task")

@app.post("/api/ingest/crawl", status_code=202)
async def trigger_crawl_ingest(request: IngestRequest):
    """Trigger URL crawling respecting robots.txt"""
    try:
        # Queue crawl tasks for each URL
        task_ids = []
        for url in request.urls:
            task = fetch_url_task.delay(url)
            task_ids.append(task.id)
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Crawl ingest queued",
                "task_ids": task_ids,
                "url_count": len(request.urls)
            }
        )
    except Exception as e:
        logger.error(f"Error queuing crawl ingest: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue crawl tasks")

@app.post("/api/extract", status_code=202)
async def trigger_extraction():
    """Trigger fact extraction from documents"""
    try:
        # Queue extraction task for unprocessed documents
        task = extract_facts_task.delay()
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Fact extraction queued",
                "task_id": task.id
            }
        )
    except Exception as e:
        logger.error(f"Error queuing extraction: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue extraction task")

@app.post("/api/compute/lcoe", status_code=200)
async def compute_lcoe(request: ComputeRequest):
    """Compute LCOE/LCOS for a scenario"""
    try:
        # Queue LCOE computation
        task = compute_lcoe_task.delay(request.scenario_id)
        
        return JSONResponse(
            content={
                "message": "LCOE computation queued",
                "task_id": task.id,
                "scenario_id": request.scenario_id
            }
        )
    except Exception as e:
        logger.error(f"Error computing LCOE: {e}")
        raise HTTPException(status_code=500, detail="Failed to compute LCOE")

@app.get("/api/rankings", response_model=List[RankingResponse])
async def get_rankings(
    scenario_id: int = Query(..., description="Scenario ID for rankings"),
    db: Database = Depends(get_db)
):
    """Get ranked energy solutions for a scenario"""
    try:
        query = """
            SELECT 
                r.entity_id,
                e.name,
                e.manufacturer,
                e.model,
                r.lcoe_usd_per_kwh,
                r.breakdown,
                r.computed_at
            FROM results_lcoe r
            JOIN entities e ON r.entity_id = e.id
            WHERE r.scenario_id = $1
            ORDER BY r.lcoe_usd_per_kwh ASC
        """
        
        rows = await db.fetch_all(query, scenario_id)
        
        return [
            RankingResponse(
                entity_id=row['entity_id'],
                name=row['name'],
                manufacturer=row['manufacturer'],
                model=row['model'],
                lcoe_usd_per_kwh=row['lcoe_usd_per_kwh'],
                breakdown=row['breakdown'],
                computed_at=row['computed_at']
            )
            for row in rows
        ]
        
    except Exception as e:
        logger.error(f"Error retrieving rankings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve rankings")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
