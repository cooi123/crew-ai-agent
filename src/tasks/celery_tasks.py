from src.configs.celery_config import celery_app
from crewai_primer_maker.main import runAgentPrimer
from sales_personalized_email.main import run as SalesPersonalizedEmailSAgentRun
from sales_personalized_email.models import SalesAgentInputModel
from text_to_schema.crew import SchemaProcessorCrew
from typing import Dict, Any, Optional

@celery_app.task(name="tasks.create_consultant_primer", bind=True, task_started=True)
def create_consultant_primer(self, data: Dict[str, Any]):
    """
    Create a consultant primer document asynchronously
    """
    task_id = self.request.id
    self.update_state(state='PROCESSING', meta={'status': 'Starting primer generation'})
    
    try:
        # Run the primer maker agent
        result = runAgentPrimer({"topic": data.get("topic", "")})
        
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
        raise

@celery_app.task(name="tasks.create_personalized_email", bind=True, task_started=True)
def create_personalized_email(self, data: Dict[str, Any]):
    """
    Create a personalized sales email asynchronously
    """
    task_id = self.request.id
    self.update_state(state='PROCESSING', meta={'status': 'Starting email generation', 'progress': 10})
    
    try:
        # Check if we need to process raw text
        if "raw_text" in data and data["raw_text"]:
            self.update_state(
                state='PROCESSING', 
                meta={'status': 'Converting text to structured data', 'progress': 30}
            )
            
            # Process through schema processor
            schema_output = SchemaProcessorCrew(SalesAgentInputModel).run(data["raw_text"])
        else:
            self.update_state(
                state='PROCESSING', 
                meta={'status': 'Using provided structured data', 'progress': 30}
            )
            
            # Use structured data directly
            schema_output = SalesAgentInputModel(**data.get("structured_data", {}))
        
        # Update progress
        self.update_state(
            state='PROCESSING', 
            meta={'status': 'Generating personalized email', 'progress': 50}
        )
        
        # Generate the email
        result = SalesPersonalizedEmailSAgentRun(schema_output)
        
        # Convert to dict for serialization
        result_dict = result.model_dump() if hasattr(result, 'model_dump') else result
        
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
        raise