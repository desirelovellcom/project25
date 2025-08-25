"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    PV = "pv"
    BATTERY = "battery"
    INVERTER = "inverter"
    THERMAL = "thermal"
    WIND = "wind"
    HYDRO = "hydro"
    POLICY = "policy"
    TARIFF = "tariff"

class EntityBase(BaseModel):
    name: str = Field(..., description="Entity name")
    type: EntityType = Field(..., description="Entity type")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    model: Optional[str] = Field(None, description="Model name")
    version: Optional[str] = Field(None, description="Version identifier")

class EntityCreate(EntityBase):
    pass

class EntityResponse(EntityBase):
    id: int = Field(..., description="Entity ID")

class IngestRequest(BaseModel):
    query_set: Optional[List[str]] = Field(None, description="Search queries for seed search")
    urls: Optional[List[str]] = Field(None, description="URLs to crawl")

class ComputeRequest(BaseModel):
    scenario_id: int = Field(..., description="Scenario ID for LCOE computation")

class RankingResponse(BaseModel):
    entity_id: int = Field(..., description="Entity ID")
    name: str = Field(..., description="Entity name")
    manufacturer: Optional[str] = Field(None, description="Manufacturer")
    model: Optional[str] = Field(None, description="Model")
    lcoe_usd_per_kwh: float = Field(..., description="LCOE in USD per kWh")
    breakdown: Dict[str, Any] = Field(..., description="Cost breakdown details")
    computed_at: datetime = Field(..., description="Computation timestamp")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Service health status")
