from pydantic import BaseModel

class PersonalizedEmail(BaseModel):
    subject_line: str
    email_body: str
    follow_up_notes: str