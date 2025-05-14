from pydantic import BaseModel, Field

class AgentInputModel(BaseModel):
    name: str = Field(
        ..., 
        description="The prospect's full name"
    )
    title: str = Field(
        ..., 
        description="The prospect's job title or position"
    )
    company: str = Field(
        ..., 
        description="The company or organization the prospect works for"
    )
    industry: str = Field(
        ..., 
        description="The industry sector the company operates in"
    )
    linkedin_url: str = Field(
        ..., 
        description="LinkedIn profile URL of the prospect"
    )
    our_product: str = Field(
        ..., 
        description="Name of the product being pitched to the prospect"
    )
    product_url: str = Field(
        ..., 
        description="URL with more information about the product"
    )
    my_profile: str = Field(
        ..., 
        description="Information about the sender's background, role and expertise"
    )
    platform: str = Field(
        default="Email", 
        description="The platform for the message (Email or LinkedIn)"
    )