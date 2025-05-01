from src.configs.celery_config import celery_app
from crewai_primer_maker.main import runAgentPrimer
from sales_personalized_email.main import run as SalesPersonalizedEmailSAgentRun
from sales_personalized_email.models import SalesAgentInputModel
from text_to_schema.crew import SchemaProcessorCrew
from typing import Dict, Any, Optional
from src.utils.supabase_utils import create_transaction, update_transaction_status
from src.models.base_models import BaseServiceRequest
from src.utils.file_processsing import get_file_from_url, chuncker
from src.crewai_document_summariser.main import runSummarizerAgent
from src.crewai_document_summariser.models.document_summariser_input import DocumentSummariserInputModel
from src.utils.astradb_utils import create_astra_collection, initialize_astra_client, upload_documents_to_astra
import os
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

@celery_app.task(name="tasks.create_consultant_primer", bind=True, task_started=True)
def create_consultant_primer(self, request: Dict[str, Any]):
    """
    Create a consultant primer document asynchronously
    """
    task_id = self.request.id
    create_transaction(
        task_id=task_id,
        request=request,

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
        request=requestData
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

@celery_app.task(name="tasks.create_summariser_task", bind=True, task_started=True)
def create_summariser_task(self, request: Dict[str, Any]):
    """
    Create a summariser task asynchronously
    """
    task_id = self.request.id
    create_transaction(
        task_id=task_id,
        request=request
    )
    
    self.update_state(state='PROCESSING', meta={'status': 'Starting summarisation'})
    update_transaction_status(task_id, "PROCESSING")
    try:
        schema_output= SchemaProcessorCrew(DocumentSummariserInputModel).run(request)
        self.update_state(
            state='PROCESSING', 
            meta={'status': 'Generating summary', 'progress': 50}
        )
        print(f"Schema output: {schema_output}")

        result = runSummarizerAgent(schema_output)
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
        update_transaction_status(task_id, "FAILURE", result=str(e))
        raise


@celery_app.task(name="tasks.embed_documents", bind=True, task_started=True)
def create_embed_documents(self, request: Dict[str, Any]):
    
    """
    To do - need to fix multiprocesssing issues with embedding
    Embed documents asynchronously with improved memory management
    """
    print("Running embed_documents task")
    task_id = self.request.id
    
    # Get basic info from request
    project_id = request.get("projectId")
    service_id = request.get("serviceId")
    user_id = request.get("userId")
    
    create_transaction(
        task_id=task_id,
        request=request
    )

    self.update_state(state='PROCESSING', meta={'status': 'Starting embedding generation'})
    update_transaction_status(task_id, "PROCESSING")
    
    document_urls = request.get("documentUrls")
    if not document_urls:
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Task failed',
                'error': 'No document URLs provided',
                'task_id': task_id
            }
        )
        update_transaction_status(task_id, "FAILURE", error_message="No document URLs provided")
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": "No document URLs provided"
        }
    
    try:
        # Process URLs in small batches to avoid memory issues
        all_docs = []
        total_urls = len(document_urls)
        
        for i, url in enumerate(document_urls):
            self.update_state(
                state='PROCESSING', 
                meta={
                    'status': f'Loading document {i+1}/{total_urls}', 
                    'progress': int(10 + (i/total_urls) * 20)
                }
            )
            
            try:
                docs = get_file_from_url(url)
                
                # Add source metadata to documents
                if isinstance(docs, list):
                    for idx, doc in enumerate(docs):
                        if hasattr(doc, 'metadata'):
                            doc.metadata['source_url'] = url
                            doc.metadata['source_index'] = f"doc_{i}_{idx}"
                    all_docs.extend(docs)
                else:
                    if hasattr(docs, 'metadata'):
                        docs.metadata['source_url'] = url
                        docs.metadata['source_index'] = f"doc_{i}_0"
                    all_docs.append(docs)
                    
                
            except Exception as doc_error:
                print(f"Error processing URL {url}: {doc_error}")
                # Continue with other documents rather than failing the entire task
        
        # Check if we have any valid documents
        if not all_docs:
            raise ValueError("Could not process any documents from the provided URLs")
        
        total_docs = len(all_docs)
        self.update_state(
            state='PROCESSING', 
            meta={'status': f'Preparing to embed {total_docs} documents', 'progress': 30}
        )

        # chuncker
        chunks = chuncker(all_docs)
        # Embed documents using astra db inserting 
        # Initialize Astra client
        astra_client = initialize_astra_client(
            astra_api_endpoint=os.environ.get("ASTRA_DB_API_ENDPOINT"),
            astra_token=os.environ.get("ASTRA_DB_APPLICATION_TOKEN"),
            astra_namespace="test",
        )
        # Create collection
        collection_name = "document_summariser"
        collection = create_astra_collection(
            collection_name=collection_name,
            database=astra_client
        )
        upload_documents_to_astra(
            collection=collection,
            documents=chunks
        )
        self.update_state(
            state='PROCESSING', 
            meta={'status': 'Embedding documents', 'progress': 50}
        )
        request["collection_name"] = collection_name

        # Update transaction status to SUCCESS
        update_transaction_status(task_id, "SUCCESS", result=request)
        ## need to return request values to following tasks as well as the collection name

        return request
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Task failed',
                'error': str(e),
                'task_id': task_id
            }
        )
        update_transaction_status(task_id, "FAILURE", result=str(e))
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(e)
        }

