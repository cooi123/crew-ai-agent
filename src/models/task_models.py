from enum import Enum
from typing import Optional, List, Dict, Any, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from src.models.base_models import BaseServiceRequest

T = TypeVar('T', bound=BaseModel)

class TaskStatus(str, Enum):
    """Enum for task status values"""
    RECEIVED = "received"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ResourceType(str, Enum):
    """Enum for resource types"""
    LLM = "llm"
    EMBEDDING = "embedding"
    STORAGE = "storage"
    PROCESSING = "processing"

class TaskType(str, Enum):
    """Enum for task types"""
    TASK = "task"
    SUBTASK = "subtask"

class UsageMetrics(BaseModel):
    """Model for tracking usage metrics"""
    runtime_ms: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    tokens_total: Optional[int] = None
    resources_used: Dict[str, Any] = Field(default_factory=dict)
    resources_used_count: int = 0
    resources_used_cost: float = 0.0
    resource_type: ResourceType = ResourceType.LLM
    model_name: Optional[str] = None


class CeleryTaskRequest(BaseModel):
    """Base model for all Celery task requests"""
    # Base service request fields
    userId: str
    projectId: str
    serviceId: str
    inputData: dict
    documentUrls: Optional[List[str]] = None
    serviceUrl: Optional[str] = None
    
    # Task specific fields
    parent_transaction_id: Optional[str] = None
    task_type: TaskType = TaskType.TASK
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    callback_url: str = None

    
    @classmethod
    def from_base_request(cls, request: BaseServiceRequest, parent_transaction_id, callback_url, **kwargs) -> "CeleryTaskRequest":
        """Create a CeleryTaskRequest from a BaseServiceRequest"""
        return cls(
            userId=request.userId,
            projectId=request.projectId,
            serviceId=request.serviceId,
            inputData=request.inputData.model_dump(),
            documentUrls=request.documentUrls,
            serviceUrl=request.serviceUrl,
            parent_transaction_id=parent_transaction_id,
            callback_url=callback_url,
            **kwargs
        )
    
class TokenUsage(BaseModel):
    tokens_total: int
    prompt_tokens: int
    completion_tokens: int
    model_name: str
    
class ComputationalUsage(BaseModel):
    runtime_ms: int
    resources_used: dict
    
    
class TaskResult(BaseModel):
    """Model for task results"""
    # Result data
    result_payload: dict = {}
    result_document_urls: Optional[List[str]] = None
    error_message: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    computational_usage: Optional[ComputationalUsage] = None
    task_status: TaskStatus = TaskStatus.COMPLETED
    parent_transaction_id: str
    
    

