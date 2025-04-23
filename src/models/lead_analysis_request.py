from pydantic import BaseModel, Field
from typing import List, Optional


class LeadAnalysisRequest(BaseModel):
    company: str = Field(..., description="Name of the company being analyzed")
    product_name: str = Field(..., description="Name of the product")
    product_description: str = Field(..., description="Detailed description of the product")
    icp_description: str = Field(..., description="Description of the ideal customer profile")
    location: str = Field(..., description="Location of the search")
    webhook_url: Optional[str] = Field(None, description="URL to send the results to")