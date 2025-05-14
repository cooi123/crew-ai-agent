from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from pydantic import BaseModel
from src.models.task_models import (
    TaskStatus, TaskType, CeleryTaskRequest, TaskResult
)
from src.tasks.celery_tasks import (
    create_consultant_primer,
    create_personalized_email,
    create_summariser_task,
    create_embed_documents,
    create_schema_processor_task,
    complete_task_chain
)
from src.utils.supabase_utils import create_transaction, update_transaction_status, get_service
from src.models.base_models import BaseServiceRequest
import httpx
import os
from dotenv import load_dotenv
load_dotenv() 
app = FastAPI()

#add middleware for cors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)





class TaskResponse(BaseModel):
    """Response model for task creation"""
    task_id: str
    status: TaskStatus

@app.post("/service/run")
async def run_service(payload: BaseServiceRequest, request: Request) -> TaskResponse:
    """Universal endpoint to handle service requests
    check if the proivded service url matches the service table in the database
    if it does, trigger the task directly
    otherwise fail with a 400 error

    """

    callback_url = f"{request.base_url}task/result"
    print(f"Callback URL: {callback_url}")
    try:
        # Parse service URL
        service_url = payload.serviceUrl
        if not service_url:
            raise HTTPException(status_code=400, detail="serviceUrl is required")
        
        # Create initial transaction with 'received' status
        transaction = create_transaction(
            payload,
            description="Received request"
        )
        
        if not transaction:
            raise HTTPException(status_code=500, detail="Failed to create transaction")
            
        task_id = transaction['id']
        #check if the service url matches the service table in the database
        service_data = get_service(payload.serviceId)
        if not service_data:
            raise HTTPException(status_code=400, detail="Invalid service ID")
        
        service_url = service_data['url']
        if service_url != payload.serviceUrl:
            raise HTTPException(status_code=400, detail="Invalid service URL")
        task_request = CeleryTaskRequest.from_base_request(
            payload,
            parent_transaction_id=task_id,
            callback_url=callback_url
        )
        # Serialize to JSON-friendly dict, converting enums to the ddir values
        task_payload = task_request.model_dump(mode="json")
        print(f"Task request: {task_payload}")
        #tirgger task by doing a POST request to the service dont need to wait for the response
        async with httpx.AsyncClient() as client:
            print(f"Triggering task to {service_url}")
            response = await client.post(service_url, json=task_payload)
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to trigger task")

        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    

@app.post("/task/result")
async def recieve_task_result(result: TaskResult):
    """
    Recieve the task result from the service
    """
    # print(f"Recieved task result: {result.model_dump()}")
    try:
        update_transaction_status(transaction_id=result.parent_transaction_id, **result.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return result

def task_to_service_routing(task_request: CeleryTaskRequest) -> CeleryTaskRequest:
    """
    Route the task to the appropriate service
    for internal service would just trigger the task directly

    todo : for external service would need to perform a POST request to the service
    """
    service_endpoints = {
        "primer": "/primer",
        "email": "/personalizedEmail",
        "summariser": "/summariser",
    }
    #check mathcing service in the service_endpoints
    if task_request.serviceUrl:
        parsed_url = urlparse(task_request.serviceUrl)
        path= parsed_url.path
        for service, endpoint in service_endpoints.items():
            if path.endswith(endpoint):
                matching_service = service
                break
        else:
            raise HTTPException(status_code=400, detail="Invalid service URL")
    
    #dtermine which task to trigger first 
    task_function = None
    if matching_service == "primer":
        #trigger embedding document first 
        task_function = create_consultant_primer
        
    elif matching_service == "summariser":
        #trigger schema processor first 
        task_function = create_schema_processor_task

    elif matching_service == "email":
        #trigger email task first 
        task_function = create_personalized_email
    else:
        raise HTTPException(status_code=400, detail="Invalid service URL")
    
    #trigger the first task with embedding document first 
    chain = create_embed_documents.s(task_request.model_dump()) | task_function.s() | complete_task_chain.s()
    task = chain.apply_async()
    return task


