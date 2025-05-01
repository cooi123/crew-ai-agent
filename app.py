#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
from typing import Optional
from celery.result import AsyncResult
from src.models.base_models import BaseServiceRequest
from urllib.parse import urlparse
from src.tasks.celery_tasks import create_consultant_primer, create_personalized_email, create_embed_documents, create_summariser_task

class TaskResponse(BaseModel):
    """Response for asynchronous tasks"""
    task_id: str
    status: str
    message: str
    result: Optional[dict] = None

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

service_endpoints = {
        "primer": "/primer",
        "email": "/personalizedEmail",
        "summariser": "/summariser",
    }

@app.post("/service/run", response_model=TaskResponse)
async def run_service(
    request: BaseServiceRequest,
):
    """Universal endpoint to run any service based on service_id"""
    print(f"Request received: {request}")
    matching_service = None
    if request.serviceUrl:
        parsed_url = urlparse(request.serviceUrl)
        path = parsed_url.path
        for service, endpoint in service_endpoints.items():
            if path.endswith(endpoint):
                matching_service = service
                break
        else:
            raise HTTPException(status_code=400, detail="Invalid service URL")
    
    # Create a chain of tasks if we have documents to embed
    if len(request.documentUrls) > 0:
        print("Embedding documents")
        # Create task chain based on the service
        if matching_service == "primer":
            chain = create_embed_documents.s(request.model_dump()) | create_consultant_primer.s()
            task_result = chain()
            task_id = task_result.id
        elif matching_service == "email":
            chain = create_embed_documents.s(request.model_dump()) | create_personalized_email.s()
            task_result = chain()
            task_id = task_result.id
        elif matching_service == "summariser":
            chain = create_embed_documents.s(request.model_dump()) | create_summariser_task.s()
            task_result = chain()
            task_id = task_result.id
        else:
            # Just embed documents if no matching service or for other purposes
            task_result = create_embed_documents.delay(request.model_dump())
            task_id = task_result.id
    else:
        # No documents to embed, directly call the service task
        if matching_service == "primer":
            task_result = create_consultant_primer.delay(request.model_dump())
            task_id = task_result.id
        elif matching_service == "email":
            task_result = create_personalized_email.delay(request.model_dump())
            task_id = task_result.id
        elif matching_service == "summariser":
            task_result = create_summariser_task.delay(request.model_dump())
            task_id = task_result.id
        else:
            # Handle the case when no matching service is found
            raise HTTPException(status_code=400, detail="No valid service specified")
    
    return {
        "task_id": task_id,
        "status": "pending",
        "message": "Task is pending"
    }


def get_task_status(task_id: str):
    """Get the status of a task"""
    result = AsyncResult(task_id)
    if result.state == 'PENDING':
        return {"status": "pending", "message": "Task is pending"}
    elif result.state == 'SUCCES S':
        return {"status": "success", "message": "Task completed successfully", "result": result.result}
    elif result.state == 'FAILURE':
        return {"status": "failure", "message": str(result.info)}
    else:
        return {"status": result.state, "message": str(result.info)}
    


# async def register_service(){


# }



if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, workers=1, log_level="info", reload=False)
    print("Server started on port", port)
