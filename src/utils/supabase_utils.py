import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import json
from typing import Optional, Dict, Any, Union, List
from src.models.base_models import BaseServiceRequest
from src.models.task_models import CeleryTaskRequest, TokenUsage, ComputationalUsage
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") 

# Initialize Supabase client with service role key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Add custom exceptions at the top of the file after imports
class TransactionError(Exception):
    """Base exception for transaction-related errors"""
    pass

class TransactionNotFoundError(TransactionError):
    """Raised when a transaction is not found"""
    pass

class TransactionUpdateError(TransactionError):
    """Raised when there's an error updating a transaction"""
    pass

class InvalidInputError(TransactionError):
    """Raised when input parameters are invalid"""
    pass

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
    task_status: str,
    result_payload: Optional[Dict[str, Any]] = None,
    result_document_urls: Optional[List[str]] = None,
    error_message: Optional[str] = None,
    token_usage: Optional[Dict[str, Any]] = {},
    computation_usage: Optional[Dict[str, Any]] = {},
    description: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
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
    
    Returns:
    - Dict containing the updated transaction data
    
    Raises:
    - InvalidInputError: If required parameters are missing
    - TransactionNotFoundError: If transaction is not found
    - TransactionUpdateError: If there's an error updating the transaction
    """
    if not transaction_id:
        raise InvalidInputError("transaction_id is required")
        
    if not task_status:
        raise InvalidInputError("task_status is required")
        
    try:
        # Create update data dictionary
        update_data = {
            'status': task_status,
            'updated_at': datetime.now().isoformat()
        }
        
        # Add optional fields if they exist
        if result_payload is not None:
            update_data['result_payload'] = result_payload
        if result_document_urls is not None:
            update_data['result_document_urls'] = result_document_urls
        if error_message is not None:
            update_data['error_message'] = error_message
        if description is not None:
            update_data['description'] = description
            
        # Handle token usage metrics
        if token_usage:
            try:
                update_data.update({
                    'prompt_tokens': token_usage.get('prompt_tokens'),
                    'completion_tokens': token_usage.get('completion_tokens'),
                    'tokens_total': token_usage.get('tokens_total'),
                    'model_name': token_usage.get('model_name')
                })
            except Exception as e:
                raise TransactionUpdateError(f"Error processing token usage metrics: {str(e)}")
            
        # Handle computation usage metrics
        if computation_usage:
            try:
                update_data.update({
                    'runtime_ms': computation_usage.get('runtime_ms'),
                    'resources_used': computation_usage.get('resources_used', {})
                })
            except Exception as e:
                raise TransactionUpdateError(f"Error processing computation usage metrics: {str(e)}")
            
        # Update the transaction
        try:
            response = supabase.table('transactions').update(update_data).eq('id', transaction_id).execute()
            
            if not response.data:
                raise TransactionNotFoundError(f"Transaction {transaction_id} not found or no data returned after update")
                
            return response.data[0]
            
        except Exception as e:
            raise TransactionUpdateError(f"Error updating transaction in Supabase: {str(e)}")
            
    except TransactionError:
        # Re-raise TransactionError subclasses
        raise
    except Exception as e:
        raise TransactionUpdateError(f"Unexpected error in update_transaction_status: {str(e)}")

    

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


def get_service(service_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a service by its ID
    """
    response = supabase.table('services').select('*').eq('id', service_id).execute()
    return response.data[0] if response.data else None

