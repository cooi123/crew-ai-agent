#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from crewai_plus_lead_scoring.main import run
from crewai_customer_research.main import runAgent
import uvicorn
from src.models.lead_analysis_request import LeadAnalysisRequest
from crewai_primer_maker.main import runAgentPrimer
from crewai_primer_maker.crew import PrimerOutput
from src.models.primer_request import PrimerRequest
from crewai_customer_research.models.agent_input import AgentInput as EmailAgentInput
from crewai_customer_research.models.email_output import FinalEmailOutput
from sales_personalized_email.main import run as SalesPersonalizedEmailSAgentRun
from sales_personalized_email.models import SalesAgentInputModel, PersonalizedEmail

load_dotenv()
app = FastAPI(title="Studio Agents")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def default():
    return "Welcome to Studio Agents"

@app.post("/lead/analysis")
async def lead_analysis(request: LeadAnalysisRequest):
    try:
        user_inputs =  request.model_dump()
        print(type(user_inputs))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Invalid data provided")
    
    result = run(user_inputs)
    print(f"Result: {result.raw}")

    return Response(
            content=result.raw,
            media_type="text/markdown"
        )

@app.post("/lead/createEmail", response_model=FinalEmailOutput)
async def lead_create_email(request: EmailAgentInput):
    run = runAgent(request)
    print(f"Result: {run.raw}")
    return Response(
            content=run.raw,
            media_type="text/markdown"
        )


@app.post("/consultant/primer", response_model=PrimerOutput)
async def consultantCreatePrimer(request: PrimerRequest):
    print(f"Request: {request}")
    result = runAgentPrimer({"topic": request.topic})
    
    return result.json_dict

@app.post("/sales/personalizedEmail", response_model=PersonalizedEmail)
async def sales_personalized_email(input: SalesAgentInputModel):
    """
    Run the crew.
    """
    result = SalesPersonalizedEmailSAgentRun(input)
    result = result.model_dump()
    return {
        "subject_line": result.get("subject_line", ""),
        "email_body": result.get("email_body", ""),
        "follow_up_notes": result.get("follow_up_notes", ""),
    }
    



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="localhost", port=port, reload=True)
    print("Server started on port", port)
