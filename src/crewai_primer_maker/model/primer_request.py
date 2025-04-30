from pydantic import BaseModel, Field

class PrimerRequest(BaseModel):
    """Model for Primer request"""
    topic: str = Field(..., description="Topic for the primer")

    # tone: str = Field(..., description="Tone of the primer")
    # audience: str = Field(..., description="Audience for the primer")
    # length: int = Field(..., description="Length of the primer in words")
    # format: str = Field(..., description="Format of the primer (e.g., email, report)")
    # style: str = Field(..., description="Style of the primer (e.g., formal, informal)")