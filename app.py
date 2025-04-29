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
from pydantic import BaseModel
from src.tasks.celery_tasks import create_consultant_primer, create_personalized_email
from src.crewai_primer_maker.model.primer_request import PrimerRequest
from src.sales_personalized_email.crew import SalesPersonalizedEmailCrew
from src.sales_personalized_email.models import SalesAgentInputModel
from typing import Optional
from celery.result import AsyncResult

class TextInputRequest(BaseModel):
    """Model for raw text input"""
    raw_text: str

class TaskResponse(BaseModel):
    """Response for asynchronous tasks"""
    task_id: str
    status: str
    message: str

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


@app.post("/consultant/primer", response_model=TaskResponse)
async def consultantCreatePrimer(request: PrimerRequest):
    print(f"Request: {request}")
    task = create_consultant_primer.delay({"topic": request.topic})
    
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Primer generation has been started"
    )

@app.post("/sales/personalizedEmail", response_model=TaskResponse)
async def sales_personalized_email(text_input: Optional[TextInputRequest] = None, structured_input: Optional[SalesAgentInputModel] = None):
    """
    Run the crew asynchronously
    """
    if text_input is None and structured_input is None:
        raise HTTPException(status_code=400, detail="Either text_input or structured_input must be provided")
    
    # Prepare data for task
    if text_input:
        task_data = {"raw_text": text_input.raw_text}
    else:
        task_data = {"structured_data": structured_input.model_dump()}
    
    # Submit task to Celery
    task = create_personalized_email.delay(task_data)
    
    return TaskResponse(
        task_id=task.id,
        status="PENDING",
        message="Email generation has been queued"
    )
    
@app.get("/task/status/{task_id}", response_model=TaskResponse)
def get_task_status(task_id: str):
    """
    Get the status of a task
    """
    res = AsyncResult(task_id)
    if res.state == 'PENDING':
        return TaskResponse(
            task_id=res.id,
            status=res.state,
            message="Task is pending"
        )
    elif res.state == 'SUCCESS':
        return TaskResponse(
            task_id=res.id,
            status=res.state,
            message="Task completed successfully",
        )
    elif res.state == 'FAILURE':
        return TaskResponse(
            task_id=res.id,
            status=res.state,
            message="Task failed",
        )
    else:
        raise HTTPException(status_code=400, detail="Unknown task state")




if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="localhost", port=port, reload=True)
    print("Server started on port", port)
