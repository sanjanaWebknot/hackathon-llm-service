"""
Pydantic models for API request/response
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class GenerateRequest(BaseModel):
    appName: str = None
    problemSolved: str = None
    coreFeatures: str = None
    frontendStack: Optional[str] = None
    backendStack: Optional[str] = None
    programmingLanguage: Optional[str] = None
    database: Optional[str] = None
    apiIntegrations: Optional[str] = None
    authentication: Optional[str] = None
    rolesPermissions: Optional[str] = None
    designStyle: Optional[str] = None
    theme: Optional[str] = None
    exclusions: Optional[str] = None
    comparableApps: Optional[str] = None
    constraints: Optional[str] = None
    num_developers: Optional[int] = None


class GenerateResponse(BaseModel):
    functional_requirements: str
    prd: str
    time_estimates: Dict[str, Any]
    cost_estimates: Dict[str, Any]

