from pydantic import BaseModel, Field

# Define the expected JSON structure for the email task output
class EmailOutput(BaseModel):
    subject: str = Field(..., description="The email subject line")
    body: str = Field(..., description="The body of the outreach email")

# Define the final formatted email output
class FinalEmailOutput(BaseModel):
    subject: str = Field(..., description="Formatted subject line of the email")
    body: str = Field(..., description="Formatted body of the outreach email")

