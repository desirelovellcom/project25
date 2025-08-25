from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import HTTPBearer
import asyncpg
import psutil
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel
import kubernetes
from kubernetes import client, config
import redis
from .database import get_db_connection
from .models import OpsAudit
from .tasks import celery_app

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBearer()

class ControlAction(BaseModel):
    action: str
    target: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class ServerControlAction(BaseModel):
    action: str
    target: str
    replicas: Optional[int] = None

async def log_admin_action(user_email: str, action: str, target: str, result: Dict[str, Any]):
    """Log admin actions to audit table"""
    async with get_db_connection() as conn:
        await conn.execute("""
            INSERT INTO ops_audit (user_email, action, target, result, ts)
            VALUES ($1, $2, $3, $4, $5)
        """, user_email, action, target, json.dumps(result), datetime.utcnow())

@router.get("/db/status")
async def db_status():
    """Database health check and metrics"""
    try:
        async with get_db_connection() as conn:
            # Basic connectivity test
            health_check = await conn.fetchval("SELECT 1")
            
            # Connection count
            active_connections = await conn.fetchval("""
                SELECT count(*) FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            
            # Database size
            db_size = await conn.fetchval("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            
            # Cache hit ratio
            cache_hit_ratio = await conn.fetchval("""
                SELECT round(
                    100 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read) + 1), 2
                ) FROM pg_stat_database WHERE datname = current_database()
            """)
            
            # Replication lag (if replica exists)
            replication_lag = None
            try:
                replication_lag = await conn.fetchval("""
                    SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
                """)
            except:
                pass  # Not a replica or no replication
            
            # Table sizes
            table_sizes = await conn.fetch("""
                SELECT schemaname, tablename, 
                       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
            """)
            
            return {
                "status": "healthy" if health_check == 1 else "unhealthy",
                "active_connections": active_connections,
                "database_size": db_size,
                "cache_hit_ratio": float(cache_hit_ratio) if cache_hit_ratio else 0,
                "replication_lag_seconds": replication_lag,
                "largest_tables": [dict(row) for row in table_sizes],
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database health check failed: {str(e)}")

@router.post("/db/control")
async def db_control(action: ControlAction, background_tasks: BackgroundTasks):
    """Database control operations"""
    user_email = "admin@system"  # In real implementation, extract from JWT
    
    try:
        if action.action == "vacuum_analyze":
            # Schedule vacuum analyze as background task
            task = celery_app.send_task('apps.api.tasks.vacuum_analyze_task')
            result = {"task_id": task.id, "status": "scheduled"}
            
        elif action.action == "backup_snapshot":
            # Trigger backup
            task = celery_app.send_task('apps.api.tasks.backup_database_task')
            result = {"task_id": task.id, "status": "scheduled"}
            
        elif action.action == "promote_replica":
            # Promote read replica (AWS RDS specific)
            result = {"status": "not_implemented", "message": "Requires AWS RDS API integration"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
        
        # Log the action
        background_tasks.add_task(
            log_admin_action, user_email, action.action, "database", result
        )
        
        return result
        
    except Exception as e:
        error_result = {"status": "error", "message": str(e)}
        background_tasks.add_task(
            log_admin_action, user_email, action.action, "database", error_result
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/server/status")
async def server_status():
    """Server health and resource metrics"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Kubernetes metrics (if running in K8s)
        k8s_status = {}
        try:
            config.load_incluster_config()  # For pods running in cluster
            v1 = client.CoreV1Api()
            
            # Get pod status
            pods = v1.list_namespaced_pod(namespace="default", label_selector="app=energy-cost")
            k8s_status = {
                "pods": {
                    "total": len(pods.items),
                    "running": len([p for p in pods.items if p.status.phase == "Running"]),
                    "pending": len([p for p in pods.items if p.status.phase == "Pending"]),
                    "failed": len([p for p in pods.items if p.status.phase == "Failed"])
                }
            }
        except:
            k8s_status = {"error": "Not running in Kubernetes or no access"}
        
        # Redis/Queue status
        queue_status = {}
        try:
            r = redis.Redis(host='redis', port=6379, decode_responses=True)
            queue_status = {
                "celery_queue_length": r.llen('celery'),
                "redis_connected": r.ping()
            }
        except:
            queue_status = {"error": "Redis not accessible"}
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "kubernetes": k8s_status,
            "queue": queue_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server status check failed: {str(e)}")

@router.post("/server/control")
async def server_control(action: ServerControlAction, background_tasks: BackgroundTasks):
    """Server control operations"""
    user_email = "admin@system"  # In real implementation, extract from JWT
    
    try:
        if action.action == "scale_api" and action.replicas:
            # Scale API deployment
            config.load_incluster_config()
            apps_v1 = client.AppsV1Api()
            
            # Update deployment replicas
            apps_v1.patch_namespaced_deployment_scale(
                name="energy-cost-api",
                namespace="default",
                body={"spec": {"replicas": action.replicas}}
            )
            result = {"status": "scaled", "replicas": action.replicas, "target": "api"}
            
        elif action.action == "scale_worker" and action.replicas:
            # Scale worker deployment
            config.load_incluster_config()
            apps_v1 = client.AppsV1Api()
            
            apps_v1.patch_namespaced_deployment_scale(
                name="energy-cost-worker",
                namespace="default", 
                body={"spec": {"replicas": action.replicas}}
            )
            result = {"status": "scaled", "replicas": action.replicas, "target": "worker"}
            
        elif action.action == "restart_service":
            # Restart service by updating deployment annotation
            config.load_incluster_config()
            apps_v1 = client.AppsV1Api()
            
            restart_annotation = {"kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()}
            apps_v1.patch_namespaced_deployment(
                name=f"energy-cost-{action.target}",
                namespace="default",
                body={"spec": {"template": {"metadata": {"annotations": restart_annotation}}}}
            )
            result = {"status": "restarted", "target": action.target}
            
        elif action.action == "drain_node":
            # Mark node as unschedulable
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            
            v1.patch_node(
                name=action.target,
                body={"spec": {"unschedulable": True}}
            )
            result = {"status": "drained", "target": action.target}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {action.action}")
        
        # Log the action
        background_tasks.add_task(
            log_admin_action, user_email, action.action, action.target, result
        )
        
        return result
        
    except Exception as e:
        error_result = {"status": "error", "message": str(e)}
        background_tasks.add_task(
            log_admin_action, user_email, action.action, action.target or "unknown", error_result
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit")
async def get_audit_log(limit: int = 100):
    """Get admin action audit log"""
    async with get_db_connection() as conn:
        records = await conn.fetch("""
            SELECT user_email, action, target, result, ts
            FROM ops_audit
            ORDER BY ts DESC
            LIMIT $1
        """, limit)
        
        return [dict(record) for record in records]
