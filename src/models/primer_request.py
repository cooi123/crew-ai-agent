from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class PrimerRequest(BaseModel):
    topic: str
