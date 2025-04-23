from pydantic import BaseModel, Field

class AgentInput(BaseModel):
    """
    This class defines the input structure for the agent.
    It includes the task type and the corresponding data.
    """
    your_company_name: str = Field(..., description="Your company name")
    product_service: str = Field(..., description="Your product or services")
    client_name: str = Field(..., description="Client name")
    client_market_segment_intro: str = Field(..., description="Client market segment introduction")
    task_prompt: str = Field(..., description="Task prompt for the agent")

