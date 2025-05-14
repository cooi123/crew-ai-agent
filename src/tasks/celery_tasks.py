from celery import shared_task
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, Type
import time
import psutil
from functools import wraps
from src.utils.supabase_utils import (
    create_transaction, update_transaction_status, create_subtask,
    get_transaction, get_subtasks
)
from src.models.task_models import (
    TaskStatus, ResourceType, TaskType, UsageMetrics, TaskResult,
    CeleryTaskRequest
)
from src.models.base_models import TextInput
from src.agents import runAgentPrimer, runSalesPersonalizedEmail, runAgentTextToSchema
from src.agents.crewai_sales_personalized_email.models import SalesAgentInputModel
from src.utils.file_processsing import get_file_from_url, chuncker, embed_documents_local
from src.utils.astradb_utils import astra_client, create_astra_collection, upload_documents_to_astra, delete_astra_collection
from src.utils.shared import generate_collection_name
import os
from dotenv import load_dotenv
from src.utils.shared import generate_collection_name
load_dotenv()

def track_usage_metrics(start_time: float, resource_type: ResourceType = ResourceType.LLM) -> UsageMetrics:
    """Track usage metrics for a task"""
    end_time = time.time()
    runtime_ms = int((end_time - start_time) * 1000)
    
    # Get memory usage
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return UsageMetrics(
        runtime_ms=runtime_ms,
        resource_type=resource_type,
        resources_used={
            "memory_rss": memory_info.rss,
            "memory_vms": memory_info.vms,
            "cpu_percent": process.cpu_percent()
        }
    )

def with_transaction_tracking(task_func: Callable[..., TaskResult]) -> Callable[..., CeleryTaskRequest]:
    """
    Higher-order function to wrap agent tasks with consistent transaction handling.
    
    This wrapper ensures:
    1. Proper transaction creation
    2. Status updates at each stage
    3. Usage metrics tracking
    4. Error handling
    5. Parent task status synchronization
    6. Proper type handling for chaining
    """
    @wraps(task_func)
    def wrapper(self, request: Dict[str, Any], *args, **kwargs) -> CeleryTaskRequest:
        start_time = time.time()
        task_id = None
        
        try:
            # Parse and validate request
            task_request = CeleryTaskRequest(**request)
            
            # Get task description from docstring
            task_description = task_func.__doc__.strip() if task_func.__doc__ else "No description available"
            
            # Create transaction
            if not task_request.parent_transaction_id:
                # Main task
                transaction = create_transaction(
                    request=task_request,
                    task_id=self.request.id,
                    description=task_description
                )
            else:
                # Subtask
                transaction = create_subtask(
                    parent_task_id=task_request.parent_transaction_id,
                    request=task_request,
                    task_id=self.request.id,
                    task_type=TaskType.SUBTASK,
                    description=task_description
                )
                
            if not transaction:
                raise Exception("Failed to create transaction")
            task_id = transaction['id']
            
            # Update task state to running
            self.update_state(state='PROCESSING', meta={'status': 'Running task...'})
            update_transaction_status(task_id, TaskStatus.RUNNING)
            
            # Execute the actual task
            try:
                print("running task")
                result: TaskResult = task_func(self, task_request, *args, **kwargs)
                print("result", result)
            except Exception as e:
                update_transaction_status(task_id, TaskStatus.FAILED, error_message=str(e))
                raise e
            
            # Track usage metrics
            usage_metrics = track_usage_metrics(start_time)
            
            # Update final status
            update_transaction_status(
                task_id,
                TaskStatus.COMPLETED,
                result_payload=result.result_payload,
                computation_usage=usage_metrics.model_dump(),
                token_usage=result.usage_metrics
            )
            
            # Create new task request for chaining
            request_data = task_request.model_dump()
            input_data = request_data.pop('inputData', None)  # Remove inputData to avoid duplication
            chain_request = CeleryTaskRequest(
                **request_data,
                inputData={**input_data, **result.result_payload}
            )
            
            return chain_request.model_dump() #for chaining we need to return a dict
            
        except Exception as e:
            if task_id:
                update_transaction_status(task_id, TaskStatus.FAILED, error_message=str(e))
            raise
            
    return wrapper

@shared_task(bind=True)
@with_transaction_tracking
def create_consultant_primer(self, task_request: CeleryTaskRequest) -> TaskResult:
    """Generate a comprehensive consultant primer based on the given topic.
    This task analyzes the topic and creates a detailed primer document with key insights,
    market analysis, and strategic recommendations.
    """
    print("task id", self.request.id)
    agentOutput = runAgentPrimer(inputs={"topic": task_request.inputData.get("text","")})
    
    # Process output
    agentOutputDict = agentOutput.model_dump()
    token_usage = agentOutputDict.get("token_usage", {})
    result = agentOutputDict.get("raw", {})
    
    return TaskResult(
        task_id=self.request.id,
        status=TaskStatus.COMPLETED,
        result_payload={"unstructured_text": result},
        usage_metrics=token_usage,
    )

@shared_task(bind=True)
@with_transaction_tracking
def create_personalized_email(self, task_request: CeleryTaskRequest) -> Dict[str, Any]:
    """Create a personalized sales email based on the input data.
    This task processes the input data through a schema processor and then generates
    a customized email using the sales agent model.
    """
    # Create schema processor subtask
    schema_request = runAgentTextToSchema(
        **task_request.model_dump(),
        target_model=SalesAgentInputModel
    )
    schema_result = create_schema_processor_task.delay(schema_request.dict()).get()
    
    # Generate email
    email_result = runSalesPersonalizedEmail(schema_result.get('result_payload'))
    
    return {
        "result_payload": email_result,
        "token_usage": schema_result.get('token_usage', {}),
        "model": schema_result.get('model', "Gemini 1.5 Pro")
    }

@shared_task(bind=True)
@with_transaction_tracking
def create_summariser_task(self, task_request: CeleryTaskRequest) -> Dict[str, Any]:
    """Generate a comprehensive summary of the provided documents.
    This task processes documents through a schema processor and then creates
    a detailed summary using the summarizer agent.
    """
    # Create schema processor subtask
    schema_request = SchemaProcessorRequest(
        **task_request.dict(),
        schema_type="document",
        parent_task_id=task_request.parent_transaction_id
    )
    schema_result = create_schema_processor_task.delay(schema_request.dict()).get()
    
    # Generate summary
    summary_result = run_summariser_agent(schema_result.get('result_payload'))
    
    return {
        "result_payload": summary_result,
        "token_usage": schema_result.get('token_usage', {}),
        "model": schema_result.get('model', "Gemini 1.5 Pro")
    }

@shared_task(bind=True)
@with_transaction_tracking
def create_embed_documents(self, task_request: CeleryTaskRequest) -> TaskResult:
    """Process and embed documents into the vector database.
    This task:
    1. Processes documents in batches
    2. Creates chunks for efficient retrieval
    3. Generates embeddings
    4. Stores vectors in the database
    5. Creates a unique collection for each project
    """
    print("parent task id", task_request.parent_transaction_id)
    print("task id", self.request.id)

    if len(task_request.documentUrls) == 0:
        return TaskResult(
            result_payload={},
        )
        
    # Process documents in batches
    batch_size = 10
    results = []
    
    # Generate a valid collection name
    collection_name = generate_collection_name(task_request.projectId, task_request.serviceId)
    print(f"Creating collection: {collection_name}")
    collection = create_astra_collection(
        collection_name=collection_name,
        database=astra_client)

    for i in range(0, len(task_request.documentUrls), batch_size):
        batch_urls = task_request.documentUrls[i:i + batch_size]
        batch_results = []
        for url in batch_urls:
            file = get_file_from_url(url)
            chunks = chuncker(file, chunk_size=500, chunk_overlap=100)
            batch_results.extend(chunks)   
        upload_documents_to_astra(
            documents=batch_results,
            collection=collection
        )

    return TaskResult(
        result_payload={
            "processed_documents": len(results),
            "collection_name": collection_name
        },
    )

@shared_task(bind=True)
def create_schema_processor_task(self, request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a schema processor task"""
    start_time = time.time()
    task_request = SchemaProcessorRequest(**request)
    
    try:
        # Create transaction
        if not task_request.parent_task_id:
            # Main task
            transaction = create_transaction(
                user_id=task_request.userId,
                project_id=task_request.projectId,
                service_id=task_request.serviceId,
                task_type=TaskType.TASK,
                input_data=task_request.inputData.dict() if task_request.inputData else None,
                input_document_urls=task_request.documentUrls
            )
            if not transaction:
                raise Exception("Failed to create transaction")
            task_id = transaction['id']
        else:
            # Subtask
            transaction = create_subtask(
                parent_transaction_id=task_request.parent_task_id,
                user_id=task_request.userId,
                project_id=task_request.projectId,
                service_id=task_request.serviceId,
                task_type=TaskType.SUBTASK,
                input_data=task_request.inputData.dict() if task_request.inputData else None,
                input_document_urls=task_request.documentUrls
            )
            if not transaction:
                raise Exception("Failed to create subtask")
            task_id = transaction['id']
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'status': 'Processing schema...'})
        update_transaction_status(task_id, TaskStatus.RUNNING)
        
        # Process schema
        schema_result = run_text_to_schema(
            task_request.inputData.dict() if task_request.inputData else {},
            schema_type=task_request.schema_type
        )
        
        # Track usage metrics
        usage_metrics = track_usage_metrics(start_time)
        
        # Update transaction status
        update_transaction_status(
            task_id,
            TaskStatus.COMPLETED,
            result_payload=schema_result,
            computation_usage=usage_metrics
        )
        
        return TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            user_id=task_request.userId,
            project_id=task_request.projectId,
            service_id=task_request.serviceId,
            parent_task_id=task_request.parent_task_id,
            result_payload=schema_result,
            usage_metrics=usage_metrics
        ).dict()
        
    except Exception as e:
        if 'task_id' in locals():
            update_transaction_status(task_id, TaskStatus.FAILED, error_message=str(e))
        raise

@shared_task(bind=True)
@with_transaction_tracking
def complete_task_chain(self, task_request: CeleryTaskRequest) -> TaskResult:
    """Complete the task chain by aggregating results from all subtasks.
    This task:
    1. Retrieves all subtasks associated with the parent task
    2. Update the parent task with the final result and document urls
    """
    print("Completing task chain")
    print("Parent task id:", task_request.parent_transaction_id)
    print("Current task id:", self.request.id)

    if not task_request.parent_transaction_id:
        print("No parent task found, returning current result")
        return TaskResult(
            result_payload=task_request.inputData
        )

    # Get parent task
    parent_task = get_transaction(task_request.parent_transaction_id)
    if not parent_task:
        print("Parent task not found")
        return TaskResult(
            result_payload=task_request.inputData
        )

    # Get all subtasks
    subtasks_data = get_subtasks(task_request.parent_transaction_id)
    print("subtasks_data", subtasks_data)
    if not subtasks_data:
        print("No subtasks found")
        return TaskResult(
            result_payload=task_request.inputData
        )
    # need to get the last subtask result
    last_subtask = subtasks_data[0]
    last_subtask_result = last_subtask.get('result_payload')
    last_subtask_document_urls = last_subtask.get('result_document_urls')

    # Update parent task with aggregated results
    update_transaction_status(
        task_request.parent_transaction_id,
        TaskStatus.COMPLETED,
        result_payload=last_subtask_result,
        result_document_urls=last_subtask_document_urls
    )

    return TaskResult(
        result_payload=last_subtask_result,
        result_document_urls=last_subtask_document_urls
    )
