import requests
import os
import tempfile
from urllib.parse import urlparse
from langchain_community.vectorstores import FAISS, Redis
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    TextLoader,
    CSVLoader,
    PyPDFLoader
)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  
loaders= {
    '.txt': TextLoader,
    '.csv': CSVLoader,
    '.pdf': PyPDFLoader
}

def get_file_from_url(url: str, headers: dict = None) -> bytes:
    """
    Fetch a file from a given URL and return its content as bytes.
    
    Args:
        url (str): The URL of the file to fetch.
        headers (dict, optional): Optional headers to include in the request.
        
    Returns:
        bytes: The content of the file.
    """
    response = requests.get(url, headers=headers, stream=True, timeout=30)
    parsed_url = urlparse(url)
    path = parsed_url.path
    file_extension = os.path.splitext(path)[1]
    loader = loaders.get(file_extension)
    if loader is None:
        raise ValueError(f"Unsupported file type: {file_extension}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(response.content)
        temp_file_path = temp_file.name
    # Load the file using the appropriate loader
    loader_instance = loader(temp_file_path)   
    loaded_docs = loader_instance.load()

    os.remove(temp_file_path)  # Clean up the temporary file
    return loaded_docs


def chuncker(documents, chunk_size=1000, chunk_overlap=200):
    """
    Chunk the documents into smaller pieces.
    
    Args:
        documents (list): List of documents to chunk.
        chunk_size (int): Size of each chunk.
        chunk_overlap (int): Overlap between chunks.
        
    Returns:
        list: List of chunked documents.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        length_function=len
    )
    return text_splitter.split_documents(documents)



def embed_documents_local(documents, index_name, path, split=True, use_redis=False, redis_url="redis://localhost:6379"):
    """
    Embed the documents using SentenceTransformerEmbeddings with memory management.
    
    Args:
        documents (list): List of documents to embed.
        index_name (str): Name for the vector store index.
        path (str): Path for storing the vector store.
        split (bool): Whether to split documents into chunks.
        
    Returns:
        dict: Information about the created vector store.
    """
    # Check path and create if it doesn't exist
    if path is None:
        path = f"default/{index_name}"
    
    # Check if we have any documents
    if not documents:
        raise ValueError("No documents provided for embedding")
        
    # Limit maximum document count to avoid memory issues
    max_docs = 1000  # Adjust based on your system capability
    if len(documents) > max_docs:
        print(f"Warning: Processing only the first {max_docs} documents to avoid memory issues")
        documents = documents[:max_docs]
        
    # Process documents in batches if needed
    if split:
        try:
            print(f"Chunking {len(documents)} documents")
            documents = chuncker(documents)
            print(f"Chunked into {len(documents)} chunks")
        except Exception as e:
            print(f"Error during document chunking: {e}")
            # Handle the error by simplifying the chunking process
            from langchain.schema import Document
            
            simplified_docs = []
            for i, doc in enumerate(documents):
                try:
                    if hasattr(doc, 'page_content'):
                        simplified_docs.append(doc)
                    elif isinstance(doc, str):
                        simplified_docs.append(Document(page_content=doc))
                    else:
                        simplified_docs.append(Document(page_content=str(doc)))
                except:
                    print(f"Skipping document {i} due to processing error")
                    
            documents = simplified_docs
    
    # Initialize embeddings model with explicit CPU usage to avoid GPU issues
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})
    
    # Create vector store directory
    vectorstore_dir = os.path.join(os.getcwd(), "vectorstore", path)
    os.makedirs(vectorstore_dir, exist_ok=True)
    vectorstore_path = os.path.join(vectorstore_dir, "faiss_index")
    if use_redis:
        # Create Redis vector store
        
        print(f"Creating Redis vector store with index name '{index_name}'")
        vectorstore = Redis.from_documents(
            documents=documents,
            embedding=embeddings,
            redis_url=redis_url,
            index_name=index_name
        )
        return {
            "type": "redis",
            "index_name": index_name,
            "document_count": len(documents),
            "redis_url": redis_url
        }
    else:
        # Create FAISS vector store
        vectorstore_dir = os.path.join(os.getcwd(), "vectorstore", path)
        os.makedirs(vectorstore_dir, exist_ok=True)
        vectorstore_path = os.path.join(vectorstore_dir, "faiss_index")
        
        vectorstore = FAISS.from_documents(documents, embeddings)
        vectorstore.save_local(vectorstore_path)
        
        return {
            "type": "faiss",
            "path": vectorstore_path,
            "document_count": len(documents),
        }

def retrieve_redis_vectorstore(index_name, redis_url="redis://localhost:6379"):
    """
    Retrieve a vector store from Redis.
    
    Args:
        project_id (str): Project ID used when creating the vector store.
        redis_url (str): URL for Redis connection.
        
    Returns:
        Redis: Redis vector store.
    """
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL, 
        model_kwargs={"device": "cpu"}
    )
    
    vectorstore = Redis.from_existing_index(
        embeddings,
        redis_url=redis_url,
        index_name=index_name
    )
    
    return vectorstore


if __name__ == "__main__":
    url = "https://xpyywboavdinaejdvoxv.supabase.co/storage/v1/object/sign/documents/personal/4346760b-c202-4506-ae91-93f314f471ea/1746063088139-sample.pdf?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InN0b3JhZ2UtdXJsLXNpZ25pbmcta2V5X2E2ZjA2MzA3LTNiNjAtNGVhNi05MmJhLTUzNjk1ZDkxMzBlYiJ9.eyJ1cmwiOiJkb2N1bWVudHMvcGVyc29uYWwvNDM0Njc2MGItYzIwMi00NTA2LWFlOTEtOTNmMzE0ZjQ3MWVhLzE3NDYwNjMwODgxMzktc2FtcGxlLnBkZiIsImlhdCI6MTc0NjA2NTcyNCwiZXhwIjoxNzQ2MDY5MzI0fQ.OIqEd7w4cNvDTf1W5fRNYt360wrHnuqRofPiRhYs2aI"

    doc = get_file_from_url(url)
    print(embed_documents_local(documents=doc, index_name="test", path="test", split=True, use_redis=True, redis_url="redis://localhost:6379/0")) 

    
    