import os
from typing import List, Dict, Any, Optional
from astrapy import DataAPIClient
from astrapy.constants import VectorMetric
from astrapy.ids import UUID
from astrapy.info import CollectionDefinition, CollectionVectorOptions, VectorServiceOptions

def create_astra_collection(
    collection_name: str,
    database,
    dimension: int = 384  # Default dimension for all-MiniLM-L6-v2
):
    """
    Create a vector collection in AstraDB
    
    Args:
        collection_name: Name of the collection to create (project_id)
        database: AstraDB database client
        dimension: Dimensionality of the vector embeddings
        
    Returns:
        AstraDB collection object
    """
    try:
        collection = database.create_collection(
            collection_name,
            definition=CollectionDefinition(
                vector=CollectionVectorOptions(
                    metric=VectorMetric.COSINE,
                    service=VectorServiceOptions(
                        provider="nvidia",
                        model_name="NV-Embed-QA",
                    )
                )
            )
        )
        print(f"Collection '{collection_name}' created successfully")
        return collection
    except Exception as e:
        print(f"Error creating collection: {e}")
        # Try to get existing collection
        try:
            collection = database.collection(collection_name)
            print(f"Using existing collection '{collection_name}'")
            return collection
        except Exception as e2:
            print(f"Error accessing collection: {e2}")
            raise


def upload_documents_to_astra(
    documents: List[Any],
    collection,
    batch_size: int = 100
) -> Dict[str, Any]:
    """
    Upload document chunks to AstraDB
    
    Args:
        documents: List of document chunks to upload
        collection: AstraDB collection object
        batch_size: Number of documents to upload in each batch
        
    Returns:
        Dict with upload statistics
    """
    print(f"Uploading {len(documents)} chunks to AstraDB...")
    
    total_uploaded = 0
    
    # Process in batches
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        astra_docs = []
        
        for chunk in batch:
            # Create document with metadata
            document = {
                "$vectorize": chunk.page_content,
                "content": chunk.page_content,  # Store actual content for retrieval
                "metadata": {
                    "source": chunk.metadata.get("source", "unknown"),
                    "page": chunk.metadata.get("page", 0),
                }
            }
            astra_docs.append(document)
        
        # Insert batch into AstraDB
        result = collection.insert_many(astra_docs)
        batch_count = len(result.inserted_ids)
        total_uploaded += batch_count
        print(f"Uploaded batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}: {batch_count} documents")
    
    print(f"Upload complete! Total uploaded: {total_uploaded}")
    return {"total_documents": len(documents), "uploaded_count": total_uploaded}

def search_astra_collection(
    collection,
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search documents in AstraDB collection using vector similarity
    
    Args:
        collection: AstraDB collection object
        query: Query text to search for
        top_k: Number of results to return
        filters: Optional filters to apply to the search
        
    Returns:
        List of matched documents with their metadata
    """
    
    cursor = collection.find(
        include_similarity=True,
        sort={"$vectorize": query},
        limit=top_k,
    )
    
    return cursor.to_list()

def get_document_by_id(
    collection,
    document_id: str
) -> Dict[str, Any]:
    """
    Retrieve a specific document by ID
    
    Args:
        collection: AstraDB collection object
        document_id: ID of the document to retrieve
        
    Returns:
        Document data with metadata
    """
    result = collection.fetch(ids=[document_id])
    
    if not result or not result.get("vectors"):
        return {"error": f"No document found with ID: {document_id}"}
    
    return result["vectors"].get(document_id, {})

def initialize_astra_client(
    astra_api_endpoint: str,
    astra_token: str,
    astra_namespace: str
) -> DataAPIClient:
    """
    Initialize AstraDB client
    
    Args:
        astra_api_endpoint: AstraDB API endpoint
        astra_token: AstraDB API token
        astra_namespace: AstraDB namespace (service)
        
    Returns:
        AstraDB client object
    """
    client = DataAPIClient()

    return client.get_database(api_endpoint=astra_api_endpoint, token=astra_token, keyspace=astra_namespace)

def delete_astra_collection(
    collection_name: str,
    database: DataAPIClient
) -> None:
    """
    Delete a collection from AstraDB

    Args:
        collection_name: Name of the collection to delete
        database: AstraDB database client
    """
    database.delete_collection(collection_name)


astra_client = initialize_astra_client(
    astra_api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
    astra_token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
    astra_namespace="test"
)

if __name__ == "__main__":
    # Example usage
    from dotenv import load_dotenv
    load_dotenv()
    astra_api_endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
    astra_token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
    database =initialize_astra_client(
        astra_api_endpoint=astra_api_endpoint,
        astra_token=astra_token,
        astra_namespace="test"  # Replace with your namespace
    )
    collection_name = "temp2"  # Replace with your collection name
    collection = create_astra_collection(
        collection_name=collection_name,
        database=database
    )
    from src.utils.file_processsing import get_file_from_url, chuncker
    docs = get_file_from_url("https://xpyywboavdinaejdvoxv.supabase.co/storage/v1/object/sign/documents/personal/4346760b-c202-4506-ae91-93f314f471ea/1746020940969-Lab%20Guide%20-%20Automation%20Decision%20Services.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InN0b3JhZ2UtdXJsLXNpZ25pbmcta2V5X2E2ZjA2MzA3LTNiNjAtNGVhNi05MmJhLTUzNjk1ZDkxMzBlYiJ9.eyJ1cmwiOiJkb2N1bWVudHMvcGVyc29uYWwvNDM0Njc2MGItYzIwMi00NTA2LWFlOTEtOTNmMzE0ZjQ3MWVhLzE3NDYwMjA5NDA5NjktTGFiIEd1aWRlIC0gQXV0b21hdGlvbiBEZWNpc2lvbiBTZXJ2aWNlcy5wZGYiLCJpYXQiOjE3NDYwNjc5MTYsImV4cCI6MTc0NjA3MTUxNn0.L-fyW1cJ1s-Wigh3j0skLa4E-ZJSG5VC2Lw3DJ551mg"
)
    
    chunks = chuncker(docs, chunk_size=500, chunk_overlap=100)
    # upload_documents_to_astra(
    #     documents=chunks,
    #     collection=collection
    # )
    search_results= search_astra_collection(
        collection=collection,
        query="CP4BA",
        top_k=5
    )



    




