import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
import json
from typing import Optional, Dict, Any, Union
load_dotenv()

# Get Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_transaction(task_id, service_id, user_id, args, project_id=None, document_id=None, document_url=None, service_url=None, auth_token=None):
    """
    Create a new transaction record in Supabase
    
    Parameters:
    - task_id: Unique identifier for the task/transaction
    - service_id: ID of the service being used
    - user_id: ID of the user making the request
    - args: The input data (will be stored as custom_input)
    - project_id: ID of the project (optional)
    - document_id: ID of the document being processed (optional)
    - document_url: URL to the document (optional)
    - service_url: URL to the service (optional)
    """
    try:
        # supabase.auth.set_session(auth_token)
        print(f"Creating transaction for task_id: {task_id}")
        # Create transaction data with snake_case field names to match DB schema
        transaction_data = {
            'id': task_id,
            'service_id': service_id,
            'user_id': user_id,
            'project_id': project_id,
            'document_id': document_id,
            'document_url': document_url,
            'service_url': service_url,
            'custom_input': args,
            'created_at': datetime.now().isoformat(),
            'status': 'STARTED'  # Adding status field for tracking
        }
        
        # Remove None values
        transaction_data = {k: v for k, v in transaction_data.items() if v is not None}
        
        # Log what we're inserting (for debugging)
        print(f"Inserting transaction: {transaction_data}")
        
        # Insert into the transactions table
        # supabase.table('transaction').insert(transaction_data).execute()
        response = supabase.table('transactions').insert(transaction_data).execute()
        print(f"Transaction created: {response.data}")
        
        return response.data
    except Exception as e:
        print(f"Error creating transaction: {str(e)}")
        # Continue execution even if logging fails
        return None

def update_transaction_status(task_id, status, result=None, error_message=None):
    """
    Update an existing transaction record with new status and result
    
    Parameters:
    - task_id: ID of the transaction to update
    - status: New status (e.g., 'PROCESSING', 'SUCCESS', 'FAILURE')
    - result: Result data (will be stored as JSONB)
    - error_message: Error message if failed
    """
    try:
        update_data = {
            'status': status,
        }
        
        if status in ['SUCCESS', 'FAILURE']:
            update_data['completed_at'] = datetime.now().isoformat()
            
        if result is not None:
            # Ensure result is in a format that can be stored as JSONB
            if isinstance(result, str):
                try:
                    # Try to parse as JSON if it's a string
                    json_result = json.loads(result)
                    update_data['result'] = json_result
                except json.JSONDecodeError:
                    # If not valid JSON, store as a text field in a JSON object
                    update_data['result'] = {"text": result}
            else:
                # If it's already a dict/list, store directly
                update_data['result'] = result
            
        if error_message is not None:
            update_data['error_message'] = error_message
            
        # Log what we're updating (for debugging)
        print(f"Updating transaction {task_id} with: {update_data}")
        
        # Update the transaction in the transactions table
        response = supabase.table('transactions').update(update_data).eq('id', task_id).execute()
        
        return response.data
    except Exception as e:
        print(f"Error updating transaction: {str(e)}")
        # Continue execution even if logging fails
        return None