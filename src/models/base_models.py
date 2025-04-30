from pydantic import BaseModel, Field
from typing import Optional, Union
from uuid import UUID

# Import your existing models
from crewai_primer_maker.model.primer_request import PrimerRequest
from sales_personalized_email.models import SalesAgentInputModel

class BaseServiceRequest(BaseModel):
    """Base model for all request models with common fields"""
    projectId: Optional[Union[str, UUID]] = Field(default=None, description="UUID of the project")
    userId: Union[str, UUID] = Field(..., description="UUID of the user")
    documentId: Optional[Union[str, UUID]] = Field(default=None, description="UUID of the document")
    documentIds: Optional[list[Union[str, UUID]]] = Field(default=None, description="List of document UUIDs")
    documentUrls: Optional[list[str]] = Field(default=None, description="List of document URLs")
    serviceId: Union[str, UUID] = Field(..., description="UUID of the service")
    serviceUrl: str = Field(..., description="URL of the service")
    customInput: Optional[str] = Field(description="Text input for the service")
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility

# class Service 