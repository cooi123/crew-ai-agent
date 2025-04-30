from src.configs.celery_config import celery_app
from crewai_primer_maker.main import runAgentPrimer
from sales_personalized_email.main import run as SalesPersonalizedEmailSAgentRun
from sales_personalized_email.models import SalesAgentInputModel
from text_to_schema.crew import SchemaProcessorCrew
from typing import Dict, Any, Optional
from src.utils.supabase_utils import create_transaction, update_transaction_status
from src.models.base_models import BaseServiceRequest

@celery_app.task(name="tasks.create_consultant_primer", bind=True, task_started=True)
def create_consultant_primer(self, request: Dict[str, Any]):
    """
    Create a consultant primer document asynchronously
    """
    task_id = self.request.id
    create_transaction(
        task_id=task_id,
        service_id=request.get("serviceId"),
        user_id=request.get("userId"),
        project_id=request.get("projectId"),
        args=request.get("customInput"),
        document_id=request.get("documentId"),
        document_url=request.get("documentUrl"),
        service_url=request.get("serviceUrl"),

    )
    self.update_state(state='PROCESSING', meta={'status': 'Starting primer generation'})
    update_transaction_status(task_id, "PROCESSING")
    try:
        # Run the primer maker agent
        result = runAgentPrimer({"topic": request.get("customInput")})
        print("updaiting transaction status")
        update_transaction_status(task_id, "SUCCESS", result=result.model_dump_json())

        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": result.json_dict
        }
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Task failed',
                'error': str(e),
                'task_id': task_id
            }
        )
        update_transaction_status(task_id, "FAILURE", error_message=str(e))
        raise

@celery_app.task(name="tasks.create_personalized_email", bind=True, task_started=True)
def create_personalized_email(self, requestData: Dict[str, Any]):
    """
    Create a personalized sales email asynchronously
    """
    task_id = self.request.id
    create_transaction(
        task_id=task_id,
        service_id=requestData.get("serviceId"),
        user_id=requestData.get("userId"),
        project_id=requestData.get("projectId"),
        args=requestData.get("customInput"),
        document_id=requestData.get("documentId"),
        document_url=requestData.get("documentUrl"),
        service_url=requestData.get("serviceUrl"),
    )
    
    self.update_state(state='PROCESSING', meta={'status': 'Starting email generation', 'progress': 10})
    update_transaction_status(task_id, "PROCESSING")
    try:
        self.update_state(
                state='PROCESSING', 
                meta={'status': 'Converting text to structured data', 'progress': 30}
            )
            
            # Process through schema processor
        schema_output = SchemaProcessorCrew(SalesAgentInputModel).run(requestData["customInput"])
        # Update progress
        self.update_state(
            state='PROCESSING', 
            meta={'status': 'Generating personalized email', 'progress': 50}
        )
        
        # Generate the email
        result = SalesPersonalizedEmailSAgentRun(schema_output)
        
        # Convert to dict for serialization
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
        update_transaction_status(task_id, "SUCCESS", result=result_dict)
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "result": result_dict
        }
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Task failed',
                'error': str(e),
                'task_id': task_id
            }
        )
        update_transaction_status(task_id, "FAILURE", error_message=str(e))
        raise
