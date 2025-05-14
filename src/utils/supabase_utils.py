import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import json
from typing import Optional, Dict, Any, Union, List
from src.models.base_models import BaseServiceRequest
from src.models.task_models import CeleryTaskRequest
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") 

# Initialize Supabase client with service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def create_transaction(
    request: BaseServiceRequest | CeleryTaskRequest,
    parent_transaction_id: Optional[str] = None,
    task_id: Optional[str] = None,
    task_type: str = 'task',
    description: str = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new transaction record in Supabase
    
    Parameters:
    - request: BaseServiceRequest or CeleryTaskRequest object containing request details
    - parent_transaction_id: ID of the parent transaction (for subtasks)
    - task_type: Type of task ('task' or 'subtask')
    
    Returns:
    - Dict containing the created transaction data including the generated ID
    """
    try:
        print(f"Creating transaction for request: {request}")
        
        print(f"Input data: {request.inputData}")
        # Create transaction data with snake_case field names to match DB schema
        transaction_data = {
            'parent_transaction_id': parent_transaction_id,
            'task_id': task_id,
            'user_id': request.userId,
            'project_id': request.projectId,
            'service_id': request.serviceId,
            'task_type': task_type,
            'input_data': request.inputData if isinstance(request, CeleryTaskRequest) else request.inputData.model_dump(),
            'input_document_urls': request.documentUrls,
            'status': 'received',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'result_payload': None,
            'result_document_urls': None,
            'error_message': None,
            'resources_used': {},
            'tokens_input': None,
            'tokens_output': None,
            'tokens_total': None,
            'runtime_ms': None,
            'resources_used_count': 0,
            'resources_used_cost': 0,
            'resource_type': 'llm',  # Default to llm, can be updated later
            'model_name': None,
            'description': description
        }
        
        # Remove None values
        transaction_data = {k: v for k, v in transaction_data.items() if v is not None}
        
        print(f"Inserting transaction: {transaction_data}")
        response = supabase.table('transactions').insert(transaction_data).execute()
        print(f"Transaction created: {response.data}")
        
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        return None

def update_transaction_status(
    transaction_id: str,
    status: str,
    result_payload: Optional[Dict[str, Any]] = None,
    result_document_urls: Optional[List[str]] = None,
    error_message: Optional[str] = None,
    token_usage: Optional[Dict[str, Any]] = None,
    computation_usage: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update an existing transaction record with new status and result
    
    Parameters:
    - task_id: ID of the transaction to update
    - status: New status ('received', 'pending', 'running', 'completed', 'failed')
    - result_payload: Result data (will be stored as JSONB)
    - result_document_urls: URLs of output documents
    - error_message: Error message if failed
    - computation_usage: Dictionary containing usage metrics (tokens, runtime, costs)
    - token_usage: Dictionary containing token usage metrics (prompt, completion, total)
    """
    try:
        # First check if the task is already completed
        current_task = supabase.table('transactions').select('status').eq('id', transaction_id).execute()
        if current_task.data and current_task.data[0]['status'] == 'completed':
            print(f"Task {transaction_id} is already completed, skipping update")
            return current_task.data

        update_data = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        
        if status in ['completed', 'failed']:
            update_data['updated_at'] = datetime.now().isoformat()
        if result_payload is not None:
            # Ensure result_payload is JSON serializable
            if isinstance(result_payload, dict):
                update_data['result_payload'] = result_payload
            else:
                update_data['result_payload'] = result_payload.model_dump() if hasattr(result_payload, 'model_dump') else str(result_payload)
            
        if result_document_urls is not None:
            update_data['result_document_urls'] = result_document_urls
            
        if error_message is not None:
            update_data['error_message'] = error_message
            
        if computation_usage is not None:
            # Update usage metrics
            update_data.update({
                'prompt_tokens': token_usage.get('prompt_tokens'),
                'completion_tokens': token_usage.get('completion_tokens'),
                'tokens_total': token_usage.get('total_tokens'),
                'runtime_ms': computation_usage.get('runtime_ms'),
                'resources_used': computation_usage.get('resources_used', {}),
                'resources_used_count': computation_usage.get('resources_used_count', 0),
                'resources_used_cost': computation_usage.get('resources_used_cost', 0),
                'resource_type': computation_usage.get('resource_type', 'llm'),
                'model_name': computation_usage.get('model_name')
                
            })
            
        # Update the transaction
        response = supabase.table('transactions').update(update_data).eq('id', transaction_id).execute()
        print(f"Transaction updated: {response.data}")
        
        # If this is a subtask, check and update parent task status
        if response.data:
            transaction = response.data[0]
            if transaction.get('parent_transaction_id'):
                # Get all subtasks for the parent
                subtasks = supabase.table('transactions').select('status').eq('parent_transaction_id', transaction['parent_transaction_id']).execute()
                
                if subtasks.data:
                    # Check if all subtasks are completed
                    all_completed = all(st['status'] == 'completed' for st in subtasks.data)
                    # Check if any subtask failed
                    any_failed = any(st['status'] == 'failed' for st in subtasks.data)
                    
                    # Update parent task status
                    if any_failed:
                        parent_status = 'failed'
                    elif all_completed:
                        parent_status = 'completed'
                    else:
                        parent_status = 'running'
                        
                    # Update parent task
                    supabase.table('transactions').update({
                        'status': parent_status,
                        'updated_at': datetime.now().isoformat()
                    }).eq('id', transaction['parent_transaction_id']).execute()
        
        return response.data
    except Exception as e:
        print(f"Error updating transaction: {str(e)}")
        return None

def create_subtask(
    parent_task_id: str,
    request: CeleryTaskRequest,
    task_id: str,
    task_type: str = 'subtask',
    description: str = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new subtask transaction linked to a parent task
    
    Parameters:
    - parent_task_id: ID of the parent transaction
    - request: BaseServiceRequest object containing request details
    - task_type: Type of task (defaults to 'subtask')
    """
    # Generate a unique subtask ID (you might want to implement your own ID generation logic)
    subtask_id = f"{parent_task_id}_subtask_{datetime.now().timestamp()}"
    return create_transaction(request, parent_task_id, task_id,task_type, description)

def get_transaction(transaction_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a transaction by its ID
    """
    return supabase.table('transactions').select('*').eq('id', transaction_id).execute()


def get_subtasks(parent_task_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Get all subtasks for a parent task, sorted by created_at in descending order
    """
    response = supabase.table('transactions').select('*').eq('parent_transaction_id', parent_task_id).order('created_at', desc=True).execute()
    # Return only the list of subtask records
    return response.data if hasattr(response, 'data') else []

