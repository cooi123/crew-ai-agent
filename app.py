from fastapi import FastAPI, HTTPException
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
from src.utils.supabase_utils import create_transaction, update_transaction_status
from src.models.base_models import BaseServiceRequest

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
async def run_service(request: BaseServiceRequest) -> TaskResponse:
    """Universal endpoint to handle service requests"""
    try:
        # Parse service URL
        service_url = request.serviceUrl
        if not service_url:
            raise HTTPException(status_code=400, detail="serviceUrl is required")
            
        parsed_url = urlparse(service_url)
        service_path = parsed_url.path.strip("/")
        # Create initial transaction with 'received' status
        transaction = create_transaction(
            request,
            description="Received request"
        )
        
        if not transaction:
            raise HTTPException(status_code=500, detail="Failed to create transaction")
            
        task_id = transaction['id']
        
        # Create task request with parent task ID
        task_request = CeleryTaskRequest.from_base_request(request, parent_transaction_id=task_id)
        try:
            task_request = task_to_service_routing(task_request)
        except Exception as e:
            update_transaction_status(task_id, TaskStatus.FAILED, error_message=str(e))
            raise HTTPException(status_code=500, detail=str(e))
        
        update_transaction_status(task_id, TaskStatus.PENDING)
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING
        )
        
    except Exception as e:
        if 'task_id' in locals():
            update_transaction_status(task_id, TaskStatus.FAILED, error_message=str(e))
        raise HTTPException(status_code=500, detail=str(e)) 
    

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


