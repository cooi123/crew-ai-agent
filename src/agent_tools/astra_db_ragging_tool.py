from typing import Type, Any, Optional
from crewai.tools import BaseTool
from datetime import datetime
from pydantic import BaseModel, Field
from utils.astradb_utils import initialize_astra_client, search_astra_collection,create_astra_collection
import os
from dotenv import load_dotenv
load_dotenv()


class AstradbVectorSearchToolInput(BaseModel):
    """Input schema for the QuestionVectorSearchTool."""
    query: Optional[str] = Field(
        None, description="The search query to find relevant submissions")
    top_k: Optional[int] = Field(
        5, description="The number of documents in order of semantic simliarity to return. Default is 5.")

class AstradbVectorSearchTool(BaseTool):
    name: str = "question_vector_search_tool"
    description: str = (
        "Searches the document to find content similar to the input 'query'. The top_k can be modified to return the number of documents in order of semantic similarity. "
        "If it is found that the results are not relevant, please try to reduce the top k or the query and try again. "
    )
    args_schema: Type[BaseModel] = AstradbVectorSearchToolInput
    vectorstore: Any = None
    collection: Any = None

    def __init__(self, collection_name:str , index_name:str = "test",**kwargs):
        super().__init__()
        self.vectorstore = initialize_astra_client(
            astra_api_endpoint=os.environ.get("ASTRA_DB_API_ENDPOINT",kwargs.get("astra_api_endpoint")),
            astra_token=os.environ.get("ASTRA_DB_APPLICATION_TOKEN",kwargs.get("astra_token")),
            astra_namespace=index_name,
        )
        self.collection= create_astra_collection(collection_name=collection_name,database=self.vectorstore)

        
    def _run(self, query: str=None,top_k:int=5 ,**kwargs):
        # Perform the vector search using the vectorstore
        if query is None:
            return [{"error": "Tool received no 'query. Provide query"}]
        
        if query:
            results = search_astra_collection(collection = self.collection, query=query, top_k=top_k)
            return results