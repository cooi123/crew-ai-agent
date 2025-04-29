from pydantic import BaseModel

class AgentInputModel(BaseModel):
    name: str
    title: str
    company: str
    industry: str
    linkedin_url: str
    our_product: str
    product_url:str
    my_profile:str