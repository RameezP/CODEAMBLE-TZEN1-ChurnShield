from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class CustomerData(BaseModel):
    industry: str = Field(default="telecom")
    customer_id: Optional[str] = "CUST-001"
    data: Dict[str, Any]

class RetentionSimulateRequest(BaseModel):
    industry: str = Field(default="telecom")
    original_data: Dict[str, Any]
    modified_data: Dict[str, Any]

class AgentChatRequest(BaseModel):
    message: str
    industry: Optional[str] = "telecom"
    customer_data: Optional[Dict[str, Any]] = None

class ExplanationRequest(BaseModel):
    industry: str = Field(default="telecom")
    data: Dict[str, Any]

class StrategyRequest(BaseModel):
    industry: str = Field(default="telecom")
    customer_id: Optional[str] = "CUST-001"
    profile: Dict[str, Any] = {}
    churn_probability: float = 0.5
    risk_level: str = "MEDIUM"
    top_drivers: List[Dict[str, Any]] = []
